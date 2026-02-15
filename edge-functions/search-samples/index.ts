// Edge Function: search-samples
// Full-text search across samples with advanced filtering

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface SearchRequest {
  query?: string
  min_bpm?: number
  max_bpm?: number
  key?: string
  genre?: string
  tags?: string[]
  instrument_type?: string
  min_energy?: number
  max_energy?: number
  mood?: string
  era_decade?: string
  limit?: number
  offset?: number
  sort_by?: 'relevance' | 'downloads' | 'newest' | 'bpm'
  sort_order?: 'asc' | 'desc'
}

interface SearchResult {
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
  instrument_type: string | null
  energy_level: number | null
  mood_tags: string[] | null
  era_decade: string | null
  relevance_score?: number
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
      query,
      min_bpm,
      max_bpm,
      key,
      genre,
      tags = [],
      instrument_type,
      min_energy,
      max_energy,
      mood,
      era_decade,
      limit = 50,
      offset = 0,
      sort_by = 'relevance',
      sort_order = 'desc'
    }: SearchRequest = await req.json()

    // Build the query
    let dbQuery = supabaseClient
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
          mood_tags,
          era_decade
        )
      `)

    // Apply text search if query provided
    if (query && query.trim()) {
      dbQuery = dbQuery.textSearch('search_vector', query, {
        type: 'websearch',
        config: 'english'
      })
    }

    // Apply BPM filters
    if (min_bpm !== undefined) {
      dbQuery = dbQuery.gte('bpm', min_bpm)
    }
    if (max_bpm !== undefined) {
      dbQuery = dbQuery.lte('bpm', max_bpm)
    }

    // Apply key filter
    if (key) {
      dbQuery = dbQuery.eq('key', key)
    }

    // Apply genre filter
    if (genre) {
      dbQuery = dbQuery.eq('genre', genre)
    }

    // Apply tags filter (all tags must be present)
    if (tags.length > 0) {
      dbQuery = dbQuery.contains('tags', tags)
    }

    // Apply metadata filters through sample_metadata
    if (instrument_type) {
      dbQuery = dbQuery.eq('sample_metadata.instrument_type', instrument_type)
    }

    if (min_energy !== undefined) {
      dbQuery = dbQuery.gte('sample_metadata.energy_level', min_energy)
    }

    if (max_energy !== undefined) {
      dbQuery = dbQuery.lte('sample_metadata.energy_level', max_energy)
    }

    if (mood) {
      dbQuery = dbQuery.contains('sample_metadata.mood_tags', [mood])
    }

    if (era_decade) {
      dbQuery = dbQuery.eq('sample_metadata.era_decade', era_decade)
    }

    // Apply sorting
    switch (sort_by) {
      case 'relevance':
        if (query && query.trim()) {
          // For text search, relevance is handled by PostgreSQL
          dbQuery = dbQuery.order('upload_date', { ascending: sort_order === 'asc' })
        } else {
          dbQuery = dbQuery.order('download_count', { ascending: sort_order === 'asc' })
        }
        break
      case 'downloads':
        dbQuery = dbQuery.order('download_count', { ascending: sort_order === 'asc' })
        break
      case 'newest':
        dbQuery = dbQuery.order('upload_date', { ascending: sort_order === 'asc' })
        break
      case 'bpm':
        dbQuery = dbQuery.order('bpm', { ascending: sort_order === 'asc', nullsFirst: false })
        break
    }

    // Apply pagination
    dbQuery = dbQuery.range(offset, offset + limit - 1)

    // Execute query
    const { data: samples, error, count } = await dbQuery

    if (error) throw error

    // Transform results
    const results: SearchResult[] = samples.map((sample: any) => ({
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
      instrument_type: sample.sample_metadata?.instrument_type || null,
      energy_level: sample.sample_metadata?.energy_level || null,
      mood_tags: sample.sample_metadata?.mood_tags || null,
      era_decade: sample.sample_metadata?.era_decade || null,
    }))

    // Get total count for pagination
    const totalCount = count || results.length

    // Get available filters for UI
    const availableFilters = await getAvailableFilters(supabaseClient, {
      min_bpm,
      max_bpm,
      key,
      genre,
      instrument_type,
      min_energy,
      max_energy,
      mood,
      era_decade
    })

    return new Response(
      JSON.stringify({
        results,
        pagination: {
          total: totalCount,
          limit,
          offset,
          has_more: offset + results.length < totalCount
        },
        filters: {
          applied: {
            query,
            min_bpm,
            max_bpm,
            key,
            genre,
            tags,
            instrument_type,
            min_energy,
            max_energy,
            mood,
            era_decade
          },
          available: availableFilters
        },
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
    console.error('Error in search-samples:', error)
    
    return new Response(
      JSON.stringify({ 
        error: error.message,
        details: 'Failed to search samples' 
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500,
      }
    )
  }
})

async function getAvailableFilters(
  supabaseClient: any,
  currentFilters: any
): Promise<any> {
  const filters: any = {}

  try {
    // Get unique genres
    const { data: genres } = await supabaseClient
      .from('samples')
      .select('genre')
      .not('genre', 'is', null)
      .order('genre')

    filters.genres = [...new Set(genres?.map((g: any) => g.genre).filter(Boolean) || [])]

    // Get unique keys
    const { data: keys } = await supabaseClient
      .from('samples')
      .select('key')
      .not('key', 'is', null)
      .order('key')

    filters.keys = [...new Set(keys?.map((k: any) => k.key).filter(Boolean) || [])]

    // Get BPM range
    const { data: bpmRange } = await supabaseClient
      .from('samples')
      .select('bpm')
      .not('bpm', 'is', null)

    const bpmValues = bpmRange?.map((b: any) => b.bpm).filter((b: number) => b > 0) || []
    if (bpmValues.length > 0) {
      filters.bpm_range = {
        min: Math.min(...bpmValues),
        max: Math.max(...bpmValues),
        avg: Math.round(bpmValues.reduce((a: number, b: number) => a + b, 0) / bpmValues.length)
      }
    }

    // Get instrument types
    const { data: instruments } = await supabaseClient
      .from('sample_metadata')
      .select('instrument_type')
      .not('instrument_type', 'is', null)
      .order('instrument_type')

    filters.instrument_types = [...new Set(instruments?.map((i: any) => i.instrument_type).filter(Boolean) || [])]

    // Get energy levels
    filters.energy_levels = {
      min: 1,
      max: 10
    }

    // Get moods
    const { data: moods } = await supabaseClient
      .from('sample_metadata')
      .select('mood_tags')
      .not('mood_tags', 'is', null)

    const allMoods = new Set<string>()
    moods?.forEach((m: any) => {
      if (m.mood_tags && Array.isArray(m.mood_tags)) {
        m.mood_tags.forEach((mood: string) => allMoods.add(mood))
      }
    })
    filters.moods = Array.from(allMoods).sort()

    // Get era decades
    const { data: eras } = await supabaseClient
      .from('sample_metadata')
      .select('era_decade')
      .not('era_decade', 'is', null)
      .order('era_decade')

    filters.era_decades = [...new Set(eras?.map((e: any) => e.era_decade).filter(Boolean) || [])]

  } catch (error) {
    console.error('Error getting available filters:', error)
  }

  return filters
}