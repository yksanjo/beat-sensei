// Edge Function: get-sample-recommendations
// Returns personalized sample recommendations based on user preferences

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface RecommendationRequest {
  user_id?: string
  limit?: number
  genres?: string[]
  bpm_range?: [number, number]
  keys?: string[]
}

interface Sample {
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
}

interface Recommendation extends Sample {
  score: number
  reason: string
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

    const { user_id, limit = 10, genres, bpm_range, keys }: RecommendationRequest = await req.json()

    // If no user_id provided, return trending samples
    if (!user_id) {
      const { data: trendingSamples, error: trendingError } = await supabaseClient
        .rpc('get_trending_samples', { limit_count: limit })

      if (trendingError) throw trendingError

      return new Response(
        JSON.stringify({
          recommendations: trendingSamples.map((sample: any) => ({
            ...sample,
            score: sample.download_count / 1000,
            reason: 'Trending'
          })),
          source: 'trending'
        }),
        {
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200,
        }
      )
    }

    // Get user preferences
    const { data: preferences, error: prefError } = await supabaseClient
      .from('user_preferences')
      .select('favorite_genres, favorite_bpm_range, favorite_keys')
      .eq('user_id', user_id)
      .single()

    if (prefError && prefError.code !== 'PGRST116') {
      throw prefError
    }

    // Use provided filters or user preferences
    const targetGenres = genres || preferences?.favorite_genres || []
    const targetBpmRange = bpm_range || 
      (preferences?.favorite_bpm_range ? 
        [preferences.favorite_bpm_range.lower, preferences.favorite_bpm_range.upper] : 
        null)
    const targetKeys = keys || preferences?.favorite_keys || []

    // Build query
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
          energy_level,
          mood_tags
        )
      `)

    // Apply filters
    if (targetGenres.length > 0) {
      query = query.in('genre', targetGenres)
    }

    if (targetBpmRange) {
      query = query.gte('bpm', targetBpmRange[0]).lte('bpm', targetBpmRange[1])
    }

    if (targetKeys.length > 0) {
      query = query.in('key', targetKeys)
    }

    // Get samples
    const { data: samples, error: samplesError } = await query
      .order('download_count', { ascending: false })
      .limit(limit)

    if (samplesError) throw samplesError

    // Calculate recommendation scores
    const recommendations: Recommendation[] = samples.map((sample: any) => {
      let score = 0
      const reasons: string[] = []

      // Genre match
      if (targetGenres.length > 0 && sample.genre && targetGenres.includes(sample.genre)) {
        score += 0.3
        reasons.push('genre_match')
      }

      // BPM match
      if (targetBpmRange && sample.bpm) {
        const [minBpm, maxBpm] = targetBpmRange
        if (sample.bpm >= minBpm && sample.bpm <= maxBpm) {
          score += 0.3
          reasons.push('bpm_match')
        }
      }

      // Key match
      if (targetKeys.length > 0 && sample.key && targetKeys.includes(sample.key)) {
        score += 0.3
        reasons.push('key_match')
      }

      // Popularity boost
      score += Math.min(sample.download_count / 10000, 0.1)

      // Energy level preference (if available)
      if (sample.sample_metadata?.energy_level) {
        // Prefer medium-high energy (5-8)
        const energyScore = 1 - Math.abs(sample.sample_metadata.energy_level - 6.5) / 6.5
        score += energyScore * 0.1
      }

      // Determine reason
      let reason = 'Popular sample'
      if (reasons.length === 3) reason = 'Matches all preferences'
      else if (reasons.includes('genre_match') && reasons.includes('bpm_match')) reason = 'Matches genre and BPM'
      else if (reasons.includes('genre_match') && reasons.includes('key_match')) reason = 'Matches genre and key'
      else if (reasons.includes('bpm_match') && reasons.includes('key_match')) reason = 'Matches BPM and key'
      else if (reasons.includes('genre_match')) reason = 'Matches genre'
      else if (reasons.includes('bpm_match')) reason = 'Matches BPM range'
      else if (reasons.includes('key_match')) reason = 'Matches key'

      return {
        ...sample,
        score: parseFloat(score.toFixed(3)),
        reason
      }
    })

    // Sort by score
    recommendations.sort((a, b) => b.score - a.score)

    // Log recommendation for analytics
    if (recommendations.length > 0 && user_id) {
      await supabaseClient
        .from('recommendations')
        .insert(
          recommendations.slice(0, 3).map(rec => ({
            user_id,
            sample_id: rec.id,
            score: rec.score,
            interaction_type: 'recommendation_view'
          }))
        )
    }

    return new Response(
      JSON.stringify({
        recommendations,
        filters_applied: {
          genres: targetGenres,
          bpm_range: targetBpmRange,
          keys: targetKeys
        },
        user_id
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    )

  } catch (error) {
    console.error('Error in get-sample-recommendations:', error)
    
    return new Response(
      JSON.stringify({ 
        error: error.message,
        details: 'Failed to get recommendations' 
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500,
      }
    )
  }
})