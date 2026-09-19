import { useEffect, useState } from "react";

type OrbitEvent = {
	type: string;
	project_id: string;
	task_id: string | null;
	agent_id: string | null;
	message: string;
	timestamp: string;
};

type AgentStatus =
	| "idle"
	| "thinking"
	| "working"
	| "waiting"
	| "completed"
	| "failed";

type Agent = {
	id: string;
	name: string;
	role: string;
	status: AgentStatus;
}

function App() {
	// Current test 6 in backend /"docs"
	const [projectId, setProjectId] = useState<string | null>(
		"project-6"
	);

	const [projectName, setProjectName] = useState("");
	const [projectGoal, setProjectGoal] = useState("");
	const [events, setEvents] = useState<OrbitEvent[]>([]);

	const [agents, setAgents] = useState<Agent[]>([
		{
			id: "manager",
			name: "Manager",
			role: "Project orchestration",
			status: "idle",
		},
		{
			id: "researcher",
			name: "Researcher",
			role: "Research and information gathering",
			status: "idle",
		},
		{
			id: "coder",
			name: "Coder",
			role: "Software development",
			status: "idle",
		},
		{
			id: "reviewer",
			name: "Reviewer",
			role: "Code review and verification",
			status: "idle",
		},
	]);

	useEffect(() => {
		if (!projectId) {
			return;
		}

		const websocket = new WebSocket(
			`ws://localhost:8000/api/projects/${projectId}/events/ws`
		);

		websocket.onopen = () => {
			console.log("ORBIT WebSocket connected!");
		};

		websocket.onmessage = (event) => {
			const data: OrbitEvent = JSON.parse(event.data);

			console.log("ORBIT EVENT:", data);

			setEvents((currentEvents) => [
				...currentEvents,
				data,
			]);

			if (data.agent_id) {
				let status: AgentStatus | null = null;

				if (data.type === "agent_started") {
					status = "working";
				}

				if (data.type === "agent_completed") {
					status = "completed";
				}

				if (data.type === "agent_assigned") {
					status = "thinking";
				}

				if (status) {
					setAgents((currentAgents) =>
					currentAgents.map((agent) =>
						agent.id === data.agent_id
						? { ...agent, status }
						: agent
					)
					);
				}
			}
		};

		websocket.onerror = (error) => {
			console.error("ORBIT WebSocket error:", error);
		};

		websocket.onclose = () => {
			console.log("ORBIT WebSocket disconnected!");
		};

		return () => {
			websocket.close();
		};
	}, [projectId]);

	const createProject = async () => {
		const response = await fetch(
			"http://localhost:8000/api/projects",
			{
				method: "POST",
				headers: {
				"Content-Type": "application/json",
				},
				body: JSON.stringify({
				id: `project-${Date.now()}`,
				name: projectName,
				goal: projectGoal,
				tasks: [],
				}),
			}
		);

		if (!response.ok) {
			console.error("Failed to create project");
			return;
		}

		const project = await response.json();

		console.log("PROJECT CREATED:", project);

		setProjectId(project.id);
	};

	return (
		<div style={{ padding: "2rem", fontFamily: "Arial" }}>
			<h1>ORBIT</h1>
			<p>Autonomous Agent Manager</p>

			<hr />

			<h2>Create Project</h2>

			<input
				type="text"
				placeholder="Project name"
				value={projectName}
				onChange={(event) =>
					setProjectName(event.target.value)
				}
			/>

			<br />
			<br />

			<textarea
				placeholder="What should ORBIT accomplish?"
				value={projectGoal}
				onChange={(event) =>
					setProjectGoal(event.target.value)
				}
			/>

			<br />
			<br />

			<button onClick={createProject}>
				Create Project
			</button>

			<h2>Agents</h2>

			<div
				style={{
				display: "flex",
				gap: "1rem",
				flexWrap: "wrap",
				}}
			>
				{agents.map((agent) => (
					<div
						key={agent.id}
						style={{
						border: "1px solid #ccc",
						borderRadius: "8px",
						padding: "1rem",
						width: "200px",
						}}
					>
						<h3>{agent.name}</h3>

						<p>{agent.role}</p>

						<strong>
						{agent.status.toUpperCase()}
						</strong>
					</div>
				))}
			</div>

			<hr />

			<h2>Live Activity</h2>

			<div>
				{events.map((event, index) => (
					<div
					key={index}
					style={{
					borderBottom: "1px solid #eee",
					padding: "0.75rem 0",
						}}
					>
						<strong>{event.type}</strong>

						<div>{event.message}</div>
						<small>
						Agent: {event.agent_id ?? "system"}
						</small>
					</div>
				))}
			</div>
		</div>
	);
}

export default App;