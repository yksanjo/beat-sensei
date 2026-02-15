// Edge Function: get-trending-samples
// Returns trending samples based on recent downloads and popularity

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface TrendingRequest {
  limit?: number
  timeframe?: 'day' | 'week' | 'month' | 'all_time'
  genre?: string
  min_bpm?: number
  max_bpm?: number
}

interface TrendingSample {
  id: string
  filename: string
  title: string
  bpm: number | null
  key: string | null
  genre: string | null
  tags: string[]
  duration: number | null
  file_size: number
  download_count: number
  file_url: string
  upload_date: string
  recent_downloads: number
  trend_score: number
  instrument_type: string | null
  energy_level: number | null
}

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
      {
        auth: {
          autoRefreshToken: false,
          persistSession: false,
        },
      }
    )

    const { 
      limit = 20, 
      timeframe = 'week',
      genre,
      min_bpm,
      max_bpm 
    }: TrendingRequest = await req.json()

    // Calculate date range based on timeframe
    let dateRange = '7 days'
    switch (timeframe) {
      case 'day':
        dateRange = '1 day'
        break
      case 'week':
        dateRange = '7 days'
        break
      case 'month':
        dateRange = '30 days'
        break
      case 'all_time':
        dateRange = null
        break
    }

    // Build query for trending samples
    let query = supabaseClient
      .from('samples')
      .select(`
        id,
        filename,
        title,
        bpm,
        key,
        genre,
        tags,
        duration,
        file_size,
        download_count,
        file_url,
        upload_date,
        sample_metadata!inner (
          instrument_type,
          energy_level
        ),
        download_logs!left (
          id
        )
      `)

    // Apply genre filter if provided
    if (genre) {
      query = query.eq('genre', genre)
    }

    // Apply BPM filters if provided
    if (min_bpm !== undefined) {
      query = query.gte('bpm', min_bpm)
    }
    if (max_bpm !== undefined) {
      query = query.lte('bpm', max_bpm)
    }

    // Execute query
    const { data: samples, error } = await query

    if (error) throw error

    // Calculate trending scores
    const trendingSamples: TrendingSample[] = samples.map((sample: any) => {
      // Count recent downloads
      let recentDownloads = 0
      if (sample.download_logs && dateRange) {
        const cutoffDate = new Date()
        cutoffDate.setDate(cutoffDate.getDate() - parseInt(dateRange.split(' ')[0]))
        
        recentDownloads = sample.download_logs.filter((log: any) => {
          // Note: We'd need to filter by date in the query for production
          // This is a simplified version
          return true // Placeholder - would filter by date in production
        }).length
      } else if (!dateRange) {
        // For all_time, use total download count
        recentDownloads = sample.download_count
      }

      // Calculate trend score
      // Weight: 70% recent downloads, 30% total downloads (normalized)
      const maxRecentDownloads = Math.max(...samples.map((s: any) => 
        s.download_logs?.length || 0
      )) || 1
      const maxTotalDownloads = Math.max(...samples.map((s: any) => 
        s.download_count || 0
      )) || 1

      const recentScore = (recentDownloads / maxRecentDownloads) * 0.7
      const totalScore = ((sample.download_count || 0) / maxTotalDownloads) * 0.3
      
      // Bonus for new uploads (within last 7 days)
      let recencyBonus = 0
      if (sample.upload_date) {
        const uploadDate = new Date(sample.upload_date)
        const daysSinceUpload = (Date.now() - uploadDate.getTime()) / (1000 * 60 * 60 * 24)
        if (daysSinceUpload < 7) {
          recencyBonus = (7 - daysSinceUpload) / 70 // Up to 0.1 bonus
        }
      }

      const trendScore = recentScore + totalScore + recencyBonus

      return {
        id: sample.id,
        filename: sample.filename,
        title: sample.title,
        bpm: sample.bpm,
        key: sample.key,
        genre: sample.genre,
        tags: sample.tags || [],
        duration: sample.duration,
        file_size: sample.file_size,
        download_count: sample.download_count,
        file_url: sample.file_url,
        upload_date: sample.upload_date,
        recent_downloads: recentDownloads,
        trend_score: parseFloat(trendScore.toFixed(4)),
        instrument_type: sample.sample_metadata?.instrument_type || null,
        energy_level: sample.sample_metadata?.energy_level || null,
      }
    })

    // Sort by trend score
    trendingSamples.sort((a, b) => b.trend_score - a.trend_score)

    // Take top N results
    const topTrending = trendingSamples.slice(0, limit)

    // Get trending statistics
    const stats = await getTrendingStats(supabaseClient, dateRange)

    return new Response(
      JSON.stringify({
        trending_samples: topTrending,
        timeframe,
        limit,
        statistics: stats,
        filters_applied: {
          genre,
          min_bpm,
          max_bpm
        }
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    )

  } catch (error) {
    console.error('Error in get-trending-samples:', error)
    
    return new Response(
      JSON.stringify({ 
        error: error.message,
        details: 'Failed to get trending samples' 
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500,
      }
    )
  }
})

async function getTrendingStats(supabaseClient: any, dateRange: string | null) {
  const stats: any = {}

  try {
    // Get total downloads in timeframe
    if (dateRange) {
      const { data: recentDownloads, error: dlError } = await supabaseClient
        .from('download_logs')
        .select('id', { count: 'exact', head: true })
        .gte('downloaded_at', `now() - interval '${dateRange}'`)

      if (!dlError) {
        stats.total_recent_downloads = recentDownloads?.length || 0
      }
    }

    // Get most popular genre in timeframe
    const { data: genreStats, error: genreError } = await supabaseClient
      .rpc('get_popular_genres', { 
        timeframe_days: dateRange ? parseInt(dateRange.split(' ')[0]) : null 
      })

    if (!genreError && genreStats) {
      stats.popular_genres = genreStats
    }

    // Get average BPM of trending samples
    const { data: bpmStats, error: bpmError } = await supabaseClient
      .from('samples')
      .select('bpm')
      .not('bpm', 'is', null)
      .order('download_count', { ascending: false })
      .limit(50)

    if (!bpmError && bpmStats) {
      const validBpms = bpmStats.filter((s: any) => s.bpm > 0).map((s: any) => s.bpm)
      if (validBpms.length > 0) {
        stats.average_trending_bpm = Math.round(
          validBpms.reduce((a: number, b: number) => a + b, 0) / validBpms.length
        )
      }
    }

  } catch (error) {
    console.error('Error getting trending stats:', error)
  }

  return stats
}