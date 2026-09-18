import { useEffect, useState } from "react";
import { getHealth } from "./api/client";

function App() {
  const [backendStatus, setBackendStatus] = useState("Connecting...");

  useEffect(() => {
    getHealth()
      .then((data) => {
        setBackendStatus(data.status);
      })
      .catch(() => {
        setBackendStatus("Offline");
      });
  }, []);

  return (
    <main>
      <h1>ORBIT</h1>

      <p>AI Agent Management Platform</p>

      <p>
        Backend: <strong>{backendStatus}</strong>
      </p>
    </main>
  );
}

export default App;