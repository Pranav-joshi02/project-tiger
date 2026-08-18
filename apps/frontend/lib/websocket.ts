export function progressSocket(runId:string){return new WebSocket((import.meta.env.VITE_WS_URL||"ws://localhost:8000")+`/runs/${runId}/progress`)}
