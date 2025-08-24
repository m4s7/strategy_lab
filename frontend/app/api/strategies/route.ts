import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001'

// Proxy all strategies requests to the backend
export async function GET(request: NextRequest) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/strategies`, {
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }
    
    const data = await response.json()
    
    // Transform backend response to match frontend expectations
    const transformedData = data.map((strategy: any) => ({
      id: strategy.id,
      name: strategy.name,
      description: strategy.description,
      type: strategy.strategy_type,
      status: strategy.status,
      sharpe: strategy.sharpe,
      winRate: strategy.win_rate,
      totalTrades: strategy.total_trades,
      lastModified: strategy.last_modified,
      parameters: strategy.parameters
    }))
    
    return NextResponse.json(transformedData)
  } catch (error) {
    console.error('Failed to fetch strategies:', error)
    return NextResponse.json(
      { error: 'Failed to fetch strategies' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Transform frontend request to match backend expectations
    const backendBody = {
      name: body.name,
      description: body.description,
      strategy_type: body.type,
      status: body.status || 'draft',
      parameters: body.parameters || {}
    }
    
    const response = await fetch(`${BACKEND_URL}/api/strategies`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(backendBody),
    })
    
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }
    
    const data = await response.json()
    
    // Transform backend response to match frontend expectations
    const transformedData = {
      id: data.id,
      name: data.name,
      description: data.description,
      type: data.strategy_type,
      status: data.status,
      sharpe: data.sharpe,
      winRate: data.win_rate,
      totalTrades: data.total_trades,
      lastModified: data.last_modified,
      parameters: data.parameters
    }
    
    return NextResponse.json(transformedData)
  } catch (error) {
    console.error('Failed to create strategy:', error)
    return NextResponse.json(
      { error: 'Failed to create strategy' },
      { status: 500 }
    )
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Transform frontend request to match backend expectations
    const backendBody = {
      name: body.name,
      description: body.description,
      strategy_type: body.type,
      status: body.status,
      sharpe: body.sharpe,
      win_rate: body.winRate,
      total_trades: body.totalTrades,
      parameters: body.parameters
    }
    
    const response = await fetch(`${BACKEND_URL}/api/strategies/${body.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(backendBody),
    })
    
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }
    
    const data = await response.json()
    
    // Transform backend response to match frontend expectations
    const transformedData = {
      id: data.id,
      name: data.name,
      description: data.description,
      type: data.strategy_type,
      status: data.status,
      sharpe: data.sharpe,
      winRate: data.win_rate,
      totalTrades: data.total_trades,
      lastModified: data.last_modified,
      parameters: data.parameters
    }
    
    return NextResponse.json(transformedData)
  } catch (error) {
    console.error('Failed to update strategy:', error)
    return NextResponse.json(
      { error: 'Failed to update strategy' },
      { status: 500 }
    )
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const id = searchParams.get('id')
    
    if (!id) {
      return NextResponse.json(
        { error: 'Strategy ID required' },
        { status: 400 }
      )
    }
    
    const response = await fetch(`${BACKEND_URL}/api/strategies/${id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok && response.status !== 204) {
      throw new Error(`Backend returned ${response.status}`)
    }
    
    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Failed to delete strategy:', error)
    return NextResponse.json(
      { error: 'Failed to delete strategy' },
      { status: 500 }
    )
  }
}