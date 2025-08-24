import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001'

// Start optimization
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/optimization`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        method: body.method || 'grid',
        parameters: body.parameters || {},
        objective: body.objective || 'sharpe'
      }),
    })
    
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }
    
    const data = await response.json()
    
    // Transform backend response to match frontend expectations
    const transformedData = {
      id: data.id,
      status: data.status,
      method: body.method || 'grid',
      parameters: body.parameters || {},
      objective: body.objective || 'sharpe',
      startTime: new Date().toISOString(),
      estimatedTime: 45,
      progress: data.progress,
      currentIteration: Math.floor(data.progress),
      totalIterations: 100,
      bestResult: data.best_result
    }
    
    return NextResponse.json(transformedData)
  } catch (error) {
    console.error('Failed to start optimization:', error)
    return NextResponse.json(
      { error: 'Failed to start optimization' },
      { status: 500 }
    )
  }
}

// Get optimization status
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const id = searchParams.get('id')
    
    if (!id) {
      // Return list of recent optimizations (mock for now)
      return NextResponse.json([
        {
          id: 'opt1',
          status: 'completed',
          method: 'grid',
          objective: 'sharpe',
          startTime: '2024-01-15T10:00:00Z',
          endTime: '2024-01-15T10:45:00Z',
          bestSharpe: 2.15,
          parametersFound: {
            lookback_period: 60,
            threshold: 1.2,
            stop_loss: 0.004,
            take_profit: 0.012
          }
        },
        {
          id: 'opt2',
          status: 'running',
          method: 'genetic',
          objective: 'return',
          startTime: '2024-01-15T11:00:00Z',
          progress: 65,
          currentIteration: 65,
          totalIterations: 100
        }
      ])
    }
    
    const response = await fetch(`${BACKEND_URL}/api/optimization/${id}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json(
          { error: 'Optimization not found' },
          { status: 404 }
        )
      }
      throw new Error(`Backend returned ${response.status}`)
    }
    
    const data = await response.json()
    
    // Transform backend response to match frontend expectations
    const transformedData = {
      id: data.id,
      status: data.status,
      progress: data.progress,
      currentIteration: Math.floor(data.progress),
      totalIterations: 100,
      currentBest: data.best_result ? {
        sharpe: data.best_result.sharpe || 0,
        parameters: data.best_result
      } : null,
      message: data.status === 'completed' 
        ? 'Optimization completed successfully' 
        : `Testing parameter combination ${Math.floor(data.progress)}/100`
    }
    
    return NextResponse.json(transformedData)
  } catch (error) {
    console.error('Failed to get optimization status:', error)
    return NextResponse.json(
      { error: 'Failed to get optimization status' },
      { status: 500 }
    )
  }
}