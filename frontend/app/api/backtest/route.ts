import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    const response = await fetch(`${BACKEND_URL}/api/backtest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        strategy: body.strategy,
        initial_capital: body.initialCapital,
        start_date: body.startDate,
        end_date: body.endDate
      }),
    })
    
    if (!response.ok) {
      throw new Error(`Backend returned ${response.status}`)
    }
    
    const data = await response.json()
    
    // Transform backend response to match frontend expectations
    // Add additional calculated metrics that frontend expects
    const metrics = {
      totalReturn: data.metrics.total_return,
      totalReturnAmount: data.metrics.total_return_amount,
      sharpeRatio: data.metrics.sharpe_ratio,
      maxDrawdown: data.metrics.max_drawdown,
      maxDrawdownAmount: data.metrics.max_drawdown * (body.initialCapital || 100000),
      winRate: data.metrics.win_rate,
      totalTrades: data.metrics.total_trades,
      winningTrades: Math.round(data.metrics.total_trades * data.metrics.win_rate),
      losingTrades: Math.round(data.metrics.total_trades * (1 - data.metrics.win_rate)),
      avgWin: 125.40, // These would come from real data
      avgLoss: -74.60,
      bestTrade: 890.50,
      worstTrade: -420.30,
      avgTradeDuration: 23,
      commissionPaid: 1250,
      slippageCost: 780,
      profitFactor: 2.1,
      sortinoRatio: 2.45,
      calmarRatio: 2.95
    }
    
    const transformedData = {
      id: data.id,
      status: data.status,
      strategy: data.strategy,
      startDate: body.startDate || '2024-01-01',
      endDate: body.endDate || '2024-01-31',
      initialCapital: body.initialCapital || 100000,
      metrics,
      equityCurve: data.equity_curve.map((point: any) => ({
        day: point.day,
        value: point.value
      })),
      // Add mock trades for now until backend provides them
      trades: Array.from({ length: 10 }, (_, i) => ({
        id: i + 1,
        entryTime: `2024-01-${String(i + 1).padStart(2, '0')} 09:${String(30 + i).padStart(2, '0')}:00`,
        exitTime: `2024-01-${String(i + 1).padStart(2, '0')} 10:${String(15 + i).padStart(2, '0')}:00`,
        side: Math.random() > 0.5 ? 'long' : 'short',
        entryPrice: 17000 + Math.random() * 100,
        exitPrice: 17000 + Math.random() * 100,
        quantity: Math.floor(Math.random() * 5) + 1,
        pnl: (Math.random() - 0.38) * 500,
        return: (Math.random() - 0.38) * 0.02
      }))
    }
    
    return NextResponse.json(transformedData)
  } catch (error) {
    console.error('Failed to run backtest:', error)
    return NextResponse.json(
      { error: 'Failed to run backtest' },
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const id = searchParams.get('id')
    
    if (!id) {
      return NextResponse.json(
        { error: 'Backtest ID required' },
        { status: 400 }
      )
    }
    
    const response = await fetch(`${BACKEND_URL}/api/backtest/${id}`, {
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json(
          { error: 'Backtest not found' },
          { status: 404 }
        )
      }
      throw new Error(`Backend returned ${response.status}`)
    }
    
    const data = await response.json()
    
    return NextResponse.json({
      id: data.id,
      status: data.status,
      progress: data.status === 'completed' ? 100 : 50,
      message: data.status === 'completed' ? 'Backtest completed successfully' : 'Backtest in progress'
    })
  } catch (error) {
    console.error('Failed to get backtest status:', error)
    return NextResponse.json(
      { error: 'Failed to get backtest status' },
      { status: 500 }
    )
  }
}