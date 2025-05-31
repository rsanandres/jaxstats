import React, { useEffect, useState } from "react";

const TerminalTab = () => {
  const [log, setLog] = useState("");

  useEffect(() => {
    const fetchLog = async () => {
      try {
        const res = await fetch("/api/command-log");
        const data = await res.json();
        setLog(data.log);
      } catch (err) {
        setLog("Failed to fetch command log.");
      }
    };
    fetchLog();
    const interval = setInterval(fetchLog, 2000); // Poll every 2s
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ background: "#111", color: "#0f0", padding: "1em", fontFamily: "monospace", height: "80vh", overflow: "auto" }}>
      <pre>{log}</pre>
    </div>
  );
};

export default TerminalTab; 