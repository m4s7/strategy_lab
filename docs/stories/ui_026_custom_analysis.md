# UI_026: Custom Analysis Notebooks

## Story Details
- **Story ID**: UI_026
- **Status**: Done

## Story
As a trader, I want to create custom analysis notebooks with code, visualizations, and markdown documentation so that I can perform ad-hoc analysis and share insights with my team.

## Acceptance Criteria
1. Create and edit Jupyter-like notebooks in the browser
2. Execute Python/JavaScript code cells with strategy data access
3. Create custom visualizations using plotting libraries
4. Mix code, markdown, and rich media content
5. Save and organize notebooks in folders
6. Share notebooks with export functionality
7. Access backtest data through notebook API
8. Template library for common analyses

## Technical Requirements

### Frontend Components
```typescript
// components/notebooks/NotebookEditor.tsx
interface NotebookCell {
  id: string;
  type: 'code' | 'markdown' | 'output';
  content: string;
  language?: 'python' | 'javascript' | 'sql';
  outputs?: CellOutput[];
  metadata?: CellMetadata;
}

interface Notebook {
  id: string;
  title: string;
  cells: NotebookCell[];
  metadata: NotebookMetadata;
  createdAt: Date;
  updatedAt: Date;
}

export function NotebookEditor({ notebookId }: { notebookId?: string }) {
  const [notebook, setNotebook] = useState<Notebook>();
  const [activeCell, setActiveCell] = useState<string>();
  const [kernel, setKernel] = useState<KernelConnection>();

  // Initialize kernel connection
  useEffect(() => {
    const initKernel = async () => {
      const conn = await connectToKernel('python');
      setKernel(conn);
    };
    initKernel();
  }, []);

  const executeCell = async (cellId: string) => {
    const cell = notebook.cells.find(c => c.id === cellId);
    if (!cell || cell.type !== 'code') return;

    const result = await kernel.execute(cell.content);
    updateCellOutput(cellId, result);
  };

  return (
    <div className="notebook-editor">
      <NotebookToolbar
        notebook={notebook}
        onSave={saveNotebook}
        onExport={exportNotebook}
        onRunAll={runAllCells}
      />

      <div className="notebook-content">
        {notebook?.cells.map((cell, index) => (
          <NotebookCell
            key={cell.id}
            cell={cell}
            isActive={activeCell === cell.id}
            onActivate={() => setActiveCell(cell.id)}
            onExecute={() => executeCell(cell.id)}
            onUpdate={(content) => updateCell(cell.id, content)}
            onDelete={() => deleteCell(cell.id)}
          />
        ))}

        <AddCellButton onClick={addNewCell} />
      </div>

      <NotebookSidebar
        templates={templates}
        onTemplateSelect={loadTemplate}
      />
    </div>
  );
}
```

### Notebook Cell Component
```typescript
// components/notebooks/NotebookCell.tsx
export function NotebookCell({
  cell,
  isActive,
  onActivate,
  onExecute,
  onUpdate,
  onDelete
}: NotebookCellProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [showOutput, setShowOutput] = useState(true);

  if (cell.type === 'markdown' && !isEditing) {
    return (
      <div
        className="notebook-cell markdown-cell"
        onClick={() => { onActivate(); setIsEditing(true); }}
      >
        <MarkdownRenderer content={cell.content} />
      </div>
    );
  }

  return (
    <div className={`notebook-cell ${isActive ? 'active' : ''}`}>
      <div className="cell-toolbar">
        <span className="cell-number">[{cell.index}]</span>
        {cell.type === 'code' && (
          <>
            <Button size="sm" onClick={onExecute}>
              <Play className="h-3 w-3" />
            </Button>
            <Badge variant="outline">{cell.language}</Badge>
          </>
        )}
        <Button size="sm" variant="ghost" onClick={onDelete}>
          <Trash className="h-3 w-3" />
        </Button>
      </div>

      <div className="cell-content">
        <CodeEditor
          value={cell.content}
          language={cell.language || 'python'}
          onChange={onUpdate}
          onRun={onExecute}
          theme="notebook"
        />
      </div>

      {cell.outputs && showOutput && (
        <div className="cell-outputs">
          {cell.outputs.map((output, idx) => (
            <CellOutput key={idx} output={output} />
          ))}
        </div>
      )}
    </div>
  );
}

// Output rendering
function CellOutput({ output }: { output: CellOutput }) {
  switch (output.type) {
    case 'text':
      return <pre className="output-text">{output.data}</pre>;

    case 'html':
      return <div dangerouslySetInnerHTML={{ __html: output.data }} />;

    case 'image':
      return <img src={output.data} alt="Output" className="output-image" />;

    case 'plot':
      return <PlotlyChart data={output.data} />;

    case 'table':
      return <DataTable data={output.data} />;

    case 'error':
      return (
        <div className="output-error">
          <pre>{output.traceback}</pre>
        </div>
      );

    default:
      return <pre>{JSON.stringify(output.data, null, 2)}</pre>;
  }
}
```

### Kernel Management
```typescript
// lib/notebooks/kernel.ts
export class KernelConnection {
  private ws: WebSocket;
  private messageQueue: Map<string, (result: any) => void> = new Map();

  constructor(private kernelId: string) {
    this.connect();
  }

  private connect() {
    this.ws = new WebSocket(`ws://localhost:8888/kernels/${this.kernelId}/channels`);

    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      this.handleMessage(msg);
    };
  }

  async execute(code: string): Promise<ExecutionResult> {
    const msgId = generateId();

    const message = {
      header: {
        msg_id: msgId,
        msg_type: 'execute_request',
        session: this.kernelId
      },
      content: {
        code: code,
        silent: false,
        store_history: true
      }
    };

    return new Promise((resolve) => {
      this.messageQueue.set(msgId, resolve);
      this.ws.send(JSON.stringify(message));
    });
  }

  private handleMessage(msg: KernelMessage) {
    const callback = this.messageQueue.get(msg.parent_header.msg_id);
    if (!callback) return;

    switch (msg.msg_type) {
      case 'execute_result':
        callback({
          type: 'result',
          data: msg.content.data
        });
        break;

      case 'display_data':
        callback({
          type: 'display',
          data: msg.content.data
        });
        break;

      case 'error':
        callback({
          type: 'error',
          ename: msg.content.ename,
          evalue: msg.content.evalue,
          traceback: msg.content.traceback
        });
        break;
    }
  }
}
```

### Backend Kernel Service
```python
# api/notebooks/kernel_manager.py
import asyncio
import jupyter_client
from typing import Dict, Any
import pandas as pd
import numpy as np

class NotebookKernel:
    def __init__(self, kernel_name: str = 'python3'):
        self.km = jupyter_client.KernelManager(kernel_name=kernel_name)
        self.km.start_kernel()
        self.kc = self.km.client()
        self.kc.start_channels()
        self._inject_helpers()

    def _inject_helpers(self):
        """Inject strategy data access helpers into kernel"""
        startup_code = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# Strategy Lab API
class StrategyLab:
    @staticmethod
    def get_backtest_results(backtest_id):
        # Fetch backtest results from database
        return _fetch_backtest_results(backtest_id)

    @staticmethod
    def get_trades(backtest_id):
        # Fetch trades from database
        return pd.DataFrame(_fetch_trades(backtest_id))

    @staticmethod
    def get_market_data(symbol, start_date, end_date):
        # Fetch market data
        return pd.DataFrame(_fetch_market_data(symbol, start_date, end_date))

    @staticmethod
    def plot_pnl(results):
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=results.index,
            y=results['cumulative_pnl'],
            mode='lines',
            name='Cumulative P&L'
        ))
        return fig

sl = StrategyLab()

# Configure plotting
plt.style.use('seaborn-v0_8-darkgrid')
pd.options.display.max_rows = 100
pd.options.display.max_columns = 20
        """
        self.execute(startup_code)

    def execute(self, code: str) -> Dict[str, Any]:
        msg_id = self.kc.execute(code)

        # Collect all outputs
        outputs = []
        while True:
            try:
                msg = self.kc.get_iopub_msg(timeout=1)

                if msg['parent_header'].get('msg_id') != msg_id:
                    continue

                msg_type = msg['msg_type']
                content = msg['content']

                if msg_type == 'execute_result':
                    outputs.append({
                        'type': 'result',
                        'data': content['data']
                    })
                elif msg_type == 'display_data':
                    outputs.append({
                        'type': 'display',
                        'data': content['data']
                    })
                elif msg_type == 'error':
                    outputs.append({
                        'type': 'error',
                        'ename': content['ename'],
                        'evalue': content['evalue'],
                        'traceback': content['traceback']
                    })
                elif msg_type == 'stream':
                    outputs.append({
                        'type': 'stream',
                        'name': content['name'],
                        'text': content['text']
                    })
                elif msg_type == 'status' and content['execution_state'] == 'idle':
                    break

            except jupyter_client.Empty:
                break

        return outputs

# WebSocket handler
async def handle_kernel_websocket(websocket, path):
    kernel_id = path.split('/')[-3]
    kernel = kernels.get(kernel_id)

    if not kernel:
        kernel = NotebookKernel()
        kernels[kernel_id] = kernel

    async for message in websocket:
        msg = json.loads(message)

        if msg['header']['msg_type'] == 'execute_request':
            code = msg['content']['code']
            outputs = kernel.execute(code)

            for output in outputs:
                response = {
                    'header': {
                        'msg_type': 'execute_reply',
                        'msg_id': generate_id()
                    },
                    'parent_header': msg['header'],
                    'content': output
                }
                await websocket.send(json.dumps(response))
```

### Notebook Templates
```typescript
// lib/notebooks/templates.ts
export const notebookTemplates = [
  {
    id: 'backtest-analysis',
    name: 'Backtest Analysis',
    description: 'Comprehensive backtest result analysis',
    cells: [
      {
        type: 'markdown',
        content: '# Backtest Analysis\n\nThis notebook analyzes backtest results including performance metrics, trade analysis, and risk assessment.'
      },
      {
        type: 'code',
        language: 'python',
        content: `# Load backtest results
backtest_id = "YOUR_BACKTEST_ID"
results = sl.get_backtest_results(backtest_id)
trades = sl.get_trades(backtest_id)

print(f"Total trades: {len(trades)}")
print(f"Total P&L: ${results['total_pnl']:,.2f}")
print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")`
      },
      {
        type: 'code',
        language: 'python',
        content: `# Plot cumulative P&L
fig = sl.plot_pnl(results)
fig.update_layout(title="Cumulative P&L Over Time")
fig.show()`
      },
      {
        type: 'code',
        language: 'python',
        content: `# Trade distribution analysis
trades['pnl_pct'] = trades['pnl'] / trades['entry_value'] * 100

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# P&L distribution
axes[0, 0].hist(trades['pnl'], bins=50, alpha=0.7)
axes[0, 0].set_title('P&L Distribution')
axes[0, 0].axvline(0, color='red', linestyle='--')

# Win rate by hour
hourly_stats = trades.groupby(trades['entry_time'].dt.hour).agg({
    'pnl': ['count', 'sum', lambda x: (x > 0).mean()]
})
axes[0, 1].bar(hourly_stats.index, hourly_stats[('pnl', '<lambda>')])
axes[0, 1].set_title('Win Rate by Hour')

# Trade duration
axes[1, 0].hist(trades['duration_minutes'], bins=50, alpha=0.7)
axes[1, 0].set_title('Trade Duration (minutes)')

# Cumulative trades
axes[1, 1].plot(trades.index, range(1, len(trades) + 1))
axes[1, 1].set_title('Cumulative Trade Count')

plt.tight_layout()
plt.show()`
      }
    ]
  },
  {
    id: 'correlation-analysis',
    name: 'Strategy Correlation',
    description: 'Analyze correlations between multiple strategies',
    cells: [
      {
        type: 'markdown',
        content: '# Strategy Correlation Analysis\n\nAnalyze correlations between multiple strategies for portfolio construction.'
      },
      {
        type: 'code',
        language: 'python',
        content: `# Load multiple strategy results
strategy_ids = ["strat1", "strat2", "strat3"]
returns = {}

for sid in strategy_ids:
    results = sl.get_backtest_results(sid)
    returns[sid] = results['daily_returns']

# Create returns DataFrame
returns_df = pd.DataFrame(returns)
returns_df.head()`
      },
      {
        type: 'code',
        language: 'python',
        content: `# Calculate correlation matrix
corr_matrix = returns_df.corr()

# Create heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
            square=True, linewidths=1, cbar_kws={"shrink": 0.8})
plt.title('Strategy Correlation Matrix')
plt.show()

# Rolling correlations
rolling_corr = returns_df.rolling(window=30).corr()
fig = go.Figure()

for i, strat1 in enumerate(strategy_ids):
    for j, strat2 in enumerate(strategy_ids):
        if i < j:
            corr_series = rolling_corr[strat1].xs(strat2, level=1)
            fig.add_trace(go.Scatter(
                x=corr_series.index,
                y=corr_series.values,
                name=f'{strat1} vs {strat2}',
                mode='lines'
            ))

fig.update_layout(title='Rolling 30-Day Correlations')
fig.show()`
      }
    ]
  },
  {
    id: 'market-regime',
    name: 'Market Regime Analysis',
    description: 'Identify market regimes and strategy performance',
    cells: [
      {
        type: 'markdown',
        content: '# Market Regime Analysis\n\nIdentify different market regimes and analyze strategy performance in each.'
      },
      {
        type: 'code',
        language: 'python',
        content: `# Load market data
symbol = "NQ"
start_date = "2023-01-01"
end_date = "2023-12-31"

market_data = sl.get_market_data(symbol, start_date, end_date)
market_data['returns'] = market_data['close'].pct_change()
market_data['volatility'] = market_data['returns'].rolling(20).std() * np.sqrt(252)

# Define regimes based on volatility
market_data['regime'] = pd.qcut(market_data['volatility'], q=3,
                               labels=['Low Vol', 'Medium Vol', 'High Vol'])

# Load strategy results
results = sl.get_backtest_results("backtest_id")
daily_pnl = results['daily_pnl']`
      }
    ]
  }
];
```

### Notebook Storage
```typescript
// api/notebooks/storage.ts
interface NotebookStorage {
  save(notebook: Notebook): Promise<void>;
  load(id: string): Promise<Notebook>;
  list(userId: string): Promise<NotebookMetadata[]>;
  delete(id: string): Promise<void>;
  export(id: string, format: 'ipynb' | 'html' | 'pdf'): Promise<Blob>;
}

export class SQLiteNotebookStorage implements NotebookStorage {
  async save(notebook: Notebook): Promise<void> {
    const query = `
      INSERT OR REPLACE INTO notebooks
      (id, title, content, metadata, updated_at)
      VALUES (?, ?, ?, ?, ?)
    `;

    await db.run(query, [
      notebook.id,
      notebook.title,
      JSON.stringify(notebook.cells),
      JSON.stringify(notebook.metadata),
      new Date().toISOString()
    ]);
  }

  async export(id: string, format: 'ipynb' | 'html' | 'pdf'): Promise<Blob> {
    const notebook = await this.load(id);

    switch (format) {
      case 'ipynb':
        return this.exportToIPYNB(notebook);
      case 'html':
        return this.exportToHTML(notebook);
      case 'pdf':
        return this.exportToPDF(notebook);
    }
  }

  private exportToIPYNB(notebook: Notebook): Blob {
    const ipynb = {
      nbformat: 4,
      nbformat_minor: 5,
      metadata: {
        kernelspec: {
          display_name: "Python 3",
          language: "python",
          name: "python3"
        }
      },
      cells: notebook.cells.map(cell => ({
        cell_type: cell.type,
        source: cell.content.split('\n'),
        outputs: cell.outputs || [],
        metadata: cell.metadata || {}
      }))
    };

    return new Blob([JSON.stringify(ipynb, null, 2)], {
      type: 'application/x-ipynb+json'
    });
  }
}
```

### Code Editor Integration
```typescript
// components/notebooks/CodeEditor.tsx
import { EditorView, basicSetup } from 'codemirror';
import { python } from '@codemirror/lang-python';
import { javascript } from '@codemirror/lang-javascript';
import { sql } from '@codemirror/lang-sql';

export function CodeEditor({
  value,
  language,
  onChange,
  onRun,
  theme = 'light'
}: CodeEditorProps) {
  const editorRef = useRef<EditorView>();
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const extensions = [
      basicSetup,
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          onChange(update.state.doc.toString());
        }
      }),
      keymap.of([
        {
          key: 'Shift-Enter',
          run: () => {
            onRun();
            return true;
          }
        }
      ])
    ];

    // Add language support
    switch (language) {
      case 'python':
        extensions.push(python());
        break;
      case 'javascript':
        extensions.push(javascript());
        break;
      case 'sql':
        extensions.push(sql());
        break;
    }

    const view = new EditorView({
      doc: value,
      extensions,
      parent: containerRef.current
    });

    editorRef.current = view;

    return () => view.destroy();
  }, [language]);

  return <div ref={containerRef} className="code-editor" />;
}
```

## UI/UX Considerations
- Keyboard shortcuts for common actions (Shift+Enter to run)
- Auto-save functionality
- Syntax highlighting and auto-completion
- Collapsible cell outputs
- Drag-and-drop cell reordering
- Full-screen mode for focused work

## Testing Requirements
1. Kernel execution and output handling
2. Notebook save/load functionality
3. Code editor integration
4. Export format correctness
5. Template system functionality
6. WebSocket connection stability

## Dependencies
- UI_001: Next.js foundation
- UI_002: FastAPI backend
- UI_004: WebSocket infrastructure
- UI_015: Basic results visualization

## Story Points: 21

## Priority: Medium

## Implementation Notes
- Consider using JupyterLab components if available
- Implement kernel pooling for performance
- Add collaborative editing support later
- Cache kernel state for quick reconnection
