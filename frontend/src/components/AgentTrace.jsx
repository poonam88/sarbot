import React from "react";

function formatOutput(output) {
  if (output === null || output === undefined) {
    return "No output returned";
  }

  if (typeof output === "string") {
    return output;
  }

  return JSON.stringify(output, null, 2);
}

function AgentTrace({ toolCalls }) {
  if (!toolCalls.length) {
    return (
      <div className="card empty-state">
        <h2>Agent Trace</h2>
        <p>No tool calls have been recorded yet.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2>Agent Trace</h2>
      <div className="timeline">
        {toolCalls.map((call, index) => (
          <article className="timeline-item" key={`${call.name}-${index}`}>
            <div className="timeline-marker">{index + 1}</div>
            <div className="timeline-content">
              <div className="trace-header">
                <strong>{call.name}</strong>
                <span>{call.duration}s</span>
              </div>
              <pre>{formatOutput(call.output)}</pre>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}

export default AgentTrace;
