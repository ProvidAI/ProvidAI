'use client'

import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Spinner } from '@/components/ui/spinner'
import { useTaskStore, TaskStatus } from '@/store/taskStore'
import { CheckCircle2, Circle, XCircle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

const statusConfig: Record<TaskStatus, { label: string; progress: number; icon: React.ReactNode }> = {
  IDLE: { label: 'Ready', progress: 0, icon: <Circle className="h-4 w-4" /> },
  PLANNING: { label: 'Planning...', progress: 10, icon: <Loader2 className="h-4 w-4 animate-spin" /> },
  APPROVING_PLAN: { label: 'Approving Plan...', progress: 30, icon: <Loader2 className="h-4 w-4 animate-spin" /> },
  NEGOTIATING: { label: 'Negotiating...', progress: 40, icon: <Loader2 className="h-4 w-4 animate-spin" /> },
  PAYING: { label: 'Processing Payment...', progress: 50, icon: <Loader2 className="h-4 w-4 animate-spin" /> },
  EXECUTING: { label: 'Executing...', progress: 70, icon: <Loader2 className="h-4 w-4 animate-spin" /> },
  VERIFYING: { label: 'Verifying...', progress: 90, icon: <Loader2 className="h-4 w-4 animate-spin" /> },
  COMPLETE: { label: 'Complete', progress: 100, icon: <CheckCircle2 className="h-4 w-4 text-green-500" /> },
  FAILED: { label: 'Failed', progress: 0, icon: <XCircle className="h-4 w-4 text-red-500" /> },
}

export function TaskStatusCard() {
  const { status, plan, selectedAgent, executionLogs, result, error, progressLogs } = useTaskStore()

  const config = statusConfig[status]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {config.icon}
          Status: {config.label}
        </CardTitle>
        <CardDescription>Real-time execution logs and progress</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Progress value={config.progress} className="h-2" />

        {/* Real-time progress logs from backend */}
        {progressLogs && progressLogs.length > 0 && (
          <div className="space-y-2 max-h-80 overflow-y-auto rounded-lg bg-slate-50 p-4">
            <h4 className="font-semibold text-sm text-slate-700 mb-2">Execution Progress:</h4>
            <div className="space-y-2">
              {progressLogs.map((log, index) => {
                const isCompleted = log.status === 'completed' || log.status === 'success';
                const isFailed = log.status === 'failed' || log.status === 'error';
                const isRunning = log.status === 'running' || log.status === 'started';

                return (
                  <div
                    key={index}
                    className={cn(
                      'flex items-start gap-2 text-sm p-2 rounded border',
                      isCompleted && 'bg-green-50 border-green-200',
                      isFailed && 'bg-red-50 border-red-200',
                      isRunning && 'bg-blue-50 border-blue-200',
                      !isCompleted && !isFailed && !isRunning && 'bg-slate-100 border-slate-200'
                    )}
                  >
                    {isCompleted ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    ) : isFailed ? (
                      <XCircle className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                    ) : isRunning ? (
                      <Loader2 className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0 animate-spin" />
                    ) : (
                      <Circle className="h-4 w-4 text-slate-400 mt-0.5 flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={cn(
                          "font-semibold",
                          isCompleted && 'text-green-700',
                          isFailed && 'text-red-700',
                          isRunning && 'text-blue-700',
                          !isCompleted && !isFailed && !isRunning && 'text-slate-700'
                        )}>
                          [{log.step}]
                        </span>
                        <span className="text-xs text-slate-500">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      {log.data?.message && (
                        <p className="text-slate-600 mt-1 text-xs">
                          {log.data.message}
                        </p>
                      )}
                      {log.data?.error && (
                        <p className="text-red-600 mt-1 text-xs font-mono">
                          Error: {log.data.error}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {plan && (
          <div className="mt-4 p-4 bg-muted rounded-lg">
            <h4 className="font-semibold mb-2">Plan Details:</h4>
            <ul className="list-disc list-inside space-y-1 text-sm">
              <li>Capabilities: {plan.capabilities.join(', ')}</li>
              {plan.estimatedCost && (
                <li>Estimated Cost: ${plan.estimatedCost.toFixed(2)}</li>
              )}
              {plan.minReputation && (
                <li>Min Reputation: {plan.minReputation.toFixed(1)} stars</li>
              )}
            </ul>
          </div>
        )}

        {executionLogs.length > 0 && (
          <div className="mt-4 p-4 bg-muted rounded-lg max-h-64 overflow-y-auto">
            <h4 className="font-semibold mb-2">Execution Logs:</h4>
            <div className="space-y-1 text-xs font-mono">
              {executionLogs.map((log, index) => (
                <div key={index} className="flex gap-2">
                  <span className="text-muted-foreground">{log.timestamp}</span>
                  <span className="text-blue-500">[{log.source}]</span>
                  <span>{log.message}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {result && (
          <div className={cn(
            'mt-4 p-4 rounded-lg',
            result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          )}>
            <h4 className={cn('font-semibold mb-2', result.success ? 'text-green-800' : 'text-red-800')}>
              {result.success ? 'Task Complete!' : 'Task Failed'}
            </h4>
            {result.report && (
              <p className="text-sm">{result.report}</p>
            )}
            {result.error && (
              <p className="text-sm text-red-600">{result.error}</p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

