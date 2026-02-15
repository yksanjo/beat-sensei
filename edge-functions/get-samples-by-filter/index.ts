// Edge Function: get-samples-by-filter
// Advanced filtering with multiple criteria and pagination

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface FilterRequest {
  // Basic filters
  bpm_range?: [number, number]
  key?: string | string[]
  genre?: string | string[]
  tags?: string[]
  
  // Advanced filters
  instrument_type?: string | string[]
  energy_range?: [number, number]
  mood_tags?: string[]
  era_decade?: string | string[]
  audio_format?: string | string[]
  
  // Duration filters
  min_duration?: number
  max_duration?: number
  
  // File size filters
  min_size?: number
  max_size?: number
  
  // Date filters
  uploaded_after?: string
  uploaded_before?: string
  
  // Pagination
  limit?: number
  offset?: number
  
  // Sorting
  sort_by?: 'upload_date' | 'download_count' | 'bpm' | 'duration' | 'file_size'
  sort_order?: 'asc' | 'desc'
  
  // Special filters
  has_metadata?: boolean
  popular_only?: boolean
  recently_added?: boolean
}

interface FilteredSample {
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
  
  // Extended metadata
  metadata?: {
    instrument_type: string | null
    energy_level: number | null
    mood_tags: string[] | null
    era_decade: string | null
    audio_format: string | null
    sample_rate: number | null
    bit_depth: number | null
    channels: number | null
  }
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

    const filters: FilterRequest = await req.json()
    
    const {
      bpm_range,
      key,
      genre,
      tags = [],
      instrument_type,
      energy_range,
      mood_tags = [],
      era_decade,
      audio_format,
      min_duration,
      max_duration,
      min_size,
      max_size,
      uploaded_after,
      uploaded_before,
      limit = 50,
      offset = 0,
      sort_by = 'upload_date',
      sort_order = 'desc',
      has_metadata,
      popular_only,
      recently_added
    } = filters

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
        sample_metadata (
          instrument_type,
          energy_level,
          mood_tags,
          era_decade,
          audio_format,
          sample_rate,
          bit_depth,
          channels
        )
      `)

    // Apply BPM range filter
    if (bpm_range) {
      const [minBpm, maxBpm] = bpm_range
      if (minBpm !== undefined) {
        query = query.gte('bpm', minBpm)
      }
      if (maxBpm !== undefined) {
        query = query.lte('bpm', maxBpm)
      }
    }

    // Apply key filter (single or multiple)
    if (key) {
      if (Array.isArray(key)) {
        query = query.in('key', key)
      } else {
        query = query.eq('key', key)
      }
    }

    // Apply genre filter (single or multiple)
    if (genre) {
      if (Array.isArray(genre)) {
        query = query.in('genre', genre)
      } else {
        query = query.eq('genre', genre)
      }
    }

    // Apply tags filter (all tags must be present)
    if (tags.length > 0) {
      query = query.contains('tags', tags)
    }

    // Apply duration filters
    if (min_duration !== undefined) {
      query = query.gte('duration', min_duration)
    }
    if (max_duration !== undefined) {
      query = query.lte('duration', max_duration)
    }

    // Apply file size filters
    if (min_size !== undefined) {
      query = query.gte('file_size', min_size)
    }
    if (max_size !== undefined) {
      query = query.lte('file_size', max_size)
    }

    // Apply date filters
    if (uploaded_after) {
      query = query.gte('upload_date', uploaded_after)
    }
    if (uploaded_before) {
      query = query.lte('upload_date', uploaded_before)
    }

    // Apply special filters
    if (has_metadata) {
      query = query.not('sample_metadata', 'is', null)
    }

    if (popular_only) {
      query = query.gte('download_count', 10) // Samples with at least 10 downloads
    }

    if (recently_added) {
      const weekAgo = new Date()
      weekAgo.setDate(weekAgo.getDate() - 7)
      query = query.gte('upload_date', weekAgo.toISOString())
    }

    // Apply sorting
    let sortColumn = sort_by
    let ascending = sort_order === 'asc'
    
    switch (sort_by) {
      case 'upload_date':
        sortColumn = 'upload_date'
        break
      case 'download_count':
        sortColumn = 'download_count'
        break
      case 'bpm':
        sortColumn = 'bpm'
        break
      case 'duration':
        sortColumn = 'duration'
        break
      case 'file_size':
        sortColumn = 'file_size'
        break
    }
    
    query = query.order(sortColumn, { ascending })

    // Apply pagination
    query = query.range(offset, offset + limit - 1)

    // Execute query
    const { data: samples, error, count } = await query

    if (error) throw error

    // Transform results
    const results: FilteredSample[] = samples.map((sample: any) => ({
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
      metadata: sample.sample_metadata ? {
        instrument_type: sample.sample_metadata.instrument_type,
        energy_level: sample.sample_metadata.energy_level,
        mood_tags: sample.sample_metadata.mood_tags,
        era_decade: sample.sample_metadata.era_decade,
        audio_format: sample.sample_metadata.audio_format,
        sample_rate: sample.sample_metadata.sample_rate,
        bit_depth: sample.sample_metadata.bit_depth,
        channels: sample.sample_metadata.channels
      } : undefined
    }))

    // Apply metadata filters (these need to be done in code since they're nested)
    let filteredResults = results
    
    // Filter by instrument type
    if (instrument_type) {
      const instrumentTypes = Array.isArray(instrument_type) ? instrument_type : [instrument_type]
      filteredResults = filteredResults.filter(sample => 
        sample.metadata?.instrument_type && instrumentTypes.includes(sample.metadata.instrument_type)
      )
    }

    // Filter by energy range
    if (energy_range) {
      const [minEnergy, maxEnergy] = energy_range
      filteredResults = filteredResults.filter(sample => {
        const energy = sample.metadata?.energy_level
        return energy !== null && energy !== undefined && 
               energy >= minEnergy && energy <= maxEnergy
      })
    }

    // Filter by mood tags
    if (mood_tags.length > 0) {
      filteredResults = filteredResults.filter(sample => {
        const sampleMoods = sample.metadata?.mood_tags || []
        return mood_tags.every(mood => sampleMoods.includes(mood))
      })
    }

    // Filter by era decade
    if (era_decade) {
      const eras = Array.isArray(era_decade) ? era_decade : [era_decade]
      filteredResults = filteredResults.filter(sample => 
        sample.metadata?.era_decade && eras.includes(sample.metadata.era_decade)
      )
    }

    // Filter by audio format
    if (audio_format) {
      const formats = Array.isArray(audio_format) ? audio_format : [audio_format]
      filteredResults = filteredResults.filter(sample => 
        sample.metadata?.audio_format && formats.includes(sample.metadata.audio_format)
      )
    }

    // Get total count for pagination
    const totalCount = count || filteredResults.length

    // Apply pagination to filtered results
    const paginatedResults = filteredResults.slice(0, limit)

    // Get filter statistics
    const filterStats = await getFilterStatistics(supabaseClient, filters)

    return new Response(
      JSON.stringify({
        results: paginatedResults,
        pagination: {
          total: totalCount,
          limit,
          offset,
          has_more: offset + paginatedResults.length < totalCount
        },
        filters_applied: filters,
        statistics: filterStats,
        sort: {
          by: sort_by,
          order: sort_order
        }
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200,
      }
    )

  } catch (error) {
    console.error('Error in get-samples-by-filter:', error)
    
    return new Response(
      JSON.stringify({ 
        error: error.message,
        details: 'Failed to filter samples' 
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500,
      }
    )
  }
})

async function getFilterStatistics(supabaseClient: any, filters: FilterRequest) {
  const stats: any = {}

  try {
    // Get total sample count
    const { count: totalSamples, error: countError } = await supabaseClient
      .from('samples')
      .select('*', { count: 'exact', head: true })

    if (!countError) {
      stats.total_samples = totalSamples
    }

    // Get unique values for filters
    const { data: uniqueGenres } = await supabaseClient
      .from('samples')
      .select('genre')
      .not('genre', 'is', null)

    stats.available_genres = [...new Set(uniqueGenres?.map((g: any) => g.genre).filter(Boolean) || [])]

    const { data: uniqueKeys } = await supabaseClient
      .from('samples')
      .select('key')
      .not('key', 'is', null)

    stats.available_keys = [...new Set(uniqueKeys?.map((k: any) => k.key).filter(Boolean) || [])]

    // Get BPM statistics
    const { data: bpmStats } = await supabaseClient
      .from('samples')
      .select('bpm')
      .not('bpm', 'is', null)

    const bpmValues = bpmStats?.map((b: any) => b.bpm).filter((b: number) => b > 0) || []
    if (bpmValues.length > 0) {
      stats.bpm_statistics = {
        min: Math.min(...bpmValues),
        max: Math.max(...bpmValues),
        avg: Math.round(bpmValues.reduce((a: number, b: number) => a + b, 0) / bpmValues.length),
        common_ranges: {
          '60-80': 'Slow',
          '80-100': 'Medium',
          '100-120': 'Upbeat',
          '120-140': 'Dance',
          '140+': 'Fast'
        }
      }
    }

    // Get metadata statistics
    const { data: metadataStats } = await supabaseClient
      .from('sample_metadata')
      .select('instrument_type, energy_level, era_decade, audio_format')
      .limit(1000)

    if (metadataStats) {
      const instruments = metadataStats.map((m: any) => m.instrument_type).filter(Boolean)
      stats.available_instruments = [...new Set(instruments)]

      const eras = metadataStats.map((m: any) => m.era_decade).filter(Boolean)
      stats.available_eras = [...new Set(eras)]

      const formats = metadataStats.map((m: any) => m.audio_format).filter(Boolean)
      stats.available_formats = [...new Set(formats)]

      const energyLevels = metadataStats.map((m: any) => m.energy_level).filter((e: number) => e !== null)
      if (energyLevels.length > 0) {
        stats.energy_statistics = {
          min: Math.min(...energyLevels),
          max: Math.max(...energyLevels),
          avg: parseFloat((energyLevels.reduce((a: number, b: number) => a + b, 0) / energyLevels.length).toFixed(1))
        }
      }
    }

  } catch (error) {
    console.error('Error getting filter statistics:', error)
  }

  return stats
}