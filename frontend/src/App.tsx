import { useCallback, useEffect, useState } from "react";

import {
	ReactFlow,
	Background,
	Controls,
	MiniMap,
	useNodesState,
	useEdgesState,
	type Node,
	type Edge,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";

import AgentNode from "./components/AgentNode";

// ----------------------------------------
// TYPES
// ----------------------------------------

type AgentNodeData = {
	agentId: string;
	name: string;
	icon: string;
	role: string;
	task: string;
	status: string;
	taskStatus: string;
};

type AgentNodeType = Node<AgentNodeData, "agent">;

type Artifact = {
	path: string;
	content: string;
	description?: string | null;
};

type Task = {
	id: string;
	title: string;
	description: string;
	status: string;
	assigned_agent_id: string | null;
	dependencies: string[];

	required_capability?: string | null;

	retry_count?: number;
	max_retries?: number;
	failure_reason?: string | null;

	input_context?: string | null;
	result?: string | null;

	artifacts?: Artifact[];

	review_verdict?: string | null;
	review_feedback?: string | null;
	review_cycles?: number;
	max_review_cycles?: number;
};

type Project = {
	id: string;
	name: string;
	goal: string;
	tasks: Task[];

	replan_count?: number;
	max_replans?: number;

	final_result?: string | null;
};

type OrbitEvent = {
	type: string;
	project_id: string;
	task_id?: string | null;
	agent_id?: string | null;
	message: string;
	timestamp: string;

	data?: {
		status?: string;
		action?: string;
		reason?: string;
		title?: string;
		description?: string;
		dependencies?: string[];
		required_capability?: string | null;
		retry_count?: number;
		review_cycle?: number;
		previous_agent?: string;
		new_agent?: string;
		final_result?: string;
		replanned?: boolean;
	};
};

// ----------------------------------------
// API
// ----------------------------------------

const API_URL = "http://127.0.0.1:8000";

// ----------------------------------------
// NODE TYPES
// ----------------------------------------

const nodeTypes = {
	agent: AgentNode,
};

// ----------------------------------------
// INITIAL NODES
// ----------------------------------------

const initialNodes: AgentNodeType[] = [
	{
		id: "manager",
		type: "agent",
		position: {
			x: 350,
			y: 350,
		},
		data: {
			agentId: "manager",
			name: "Manager",
			icon: "🧠",
			role: "Project orchestration",
			task: "Waiting for project",
			status: "IDLE",
			taskStatus: "PENDING",
		},
	},

	{
		id: "researcher",
		type: "agent",
		position: {
			x: 50,
			y: 100,
		},
		data: {
			agentId: "researcher",
			name: "Researcher",
			icon: "🔎",
			role: "Research and requirements",
			task: "Waiting for task",
			status: "IDLE",
			taskStatus: "PENDING",
		},
	},

	{
		id: "coder",
		type: "agent",
		position: {
			x: 350,
			y: 100,
		},
		data: {
			agentId: "coder",
			name: "Coder",
			icon: "💻",
			role: "Implementation",
			task: "Waiting for task",
			status: "IDLE",
			taskStatus: "PENDING",
		},
	},

	{
		id: "backend_coder",
		type: "agent",
		position: {
			x: 350,
			y: 250,
		},
		data: {
			agentId: "backend_coder",
			name: "Backend Coder",
			icon: "🛠️",
			role: "Backend implementation",
			task: "Waiting for task",
			status: "IDLE",
			taskStatus: "PENDING",
		},
	},

	{
		id: "reviewer",
		type: "agent",
		position: {
			x: 650,
			y: 100,
		},
		data: {
			agentId: "reviewer",
			name: "Reviewer",
			icon: "🧪",
			role: "Review and verification",
			task: "Waiting for task",
			status: "IDLE",
			taskStatus: "PENDING",
		},
	},
];

// ----------------------------------------
// INITIAL EDGES
// ----------------------------------------

const initialEdges: Edge[] = [
	{
		id: "manager-researcher",
		source: "manager",
		target: "researcher",
		animated: true,
	},

	{
		id: "researcher-coder",
		source: "researcher",
		target: "coder",
		animated: true,
	},

	{
		id: "coder-reviewer",
		source: "coder",
		target: "reviewer",
		animated: true,
	},
];

// ----------------------------------------
// APP
// ----------------------------------------

export default function App() {
	const [nodes, setNodes, onNodesChange] =
		useNodesState<AgentNodeType>(initialNodes);

	const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

	const [project, setProject] = useState<Project | null>(null);

	const [projectId, setProjectId] = useState<string | null>(null);

	const [isRunning, setIsRunning] = useState(false);

	const [socketConnected, setSocketConnected] = useState(false);

	const [events, setEvents] = useState<OrbitEvent[]>([]);

	const [liveTasks, setLiveTasks] = useState<Task[]>([]);

	const [managerDecision, setManagerDecision] = useState<{
		action: string;
		reason: string;
	} | null>(null);

	const [goal, setGoal] = useState(
		"Build a REST API for managing projects with authentication, PostgreSQL, Docker, and tests.",
	);

	// ----------------------------------------
	// UPDATE NODE
	// ----------------------------------------

	const updateNode = useCallback(
		(agentId: string, updates: Partial<AgentNodeData>) => {
			setNodes((currentNodes) =>
				currentNodes.map((node) => {
					if (node.data.agentId !== agentId) {
						return node;
					}

					return {
						...node,
						data: {
							...node.data,
							...updates,
						},
					};
				}),
			);
		},
		[setNodes],
	);

	// ----------------------------------------
	// RESET NODES
	// ----------------------------------------

	const resetAgentNodes = useCallback(() => {
		setNodes((currentNodes) =>
			currentNodes.map((node) => ({
				...node,
				data: {
					...node.data,

					task:
						node.data.agentId === "manager"
							? "Waiting for project"
							: "Waiting for task",

					status: "IDLE",

					taskStatus: "PENDING",
				},
			})),
		);
	}, [setNodes]);

	// ----------------------------------------
	// CREATE PROJECT
	// ----------------------------------------

	const createProject = async () => {
		try {
			const newProjectId = `project-${Date.now()}`;

			const response = await fetch(`${API_URL}/api/projects`, {
				method: "POST",

				headers: {
					"Content-Type": "application/json",
				},

				body: JSON.stringify({
					id: newProjectId,
					name: "ORBIT Demo",
					goal,
					tasks: [],
				}),
			});

			if (!response.ok) {
				throw new Error(`Failed to create project: ${response.status}`);
			}

			const createdProject: Project = await response.json();

			setProject(createdProject);

			setProjectId(createdProject.id);

			setEvents([]);

			setLiveTasks([]);

			setManagerDecision(null);

			resetAgentNodes();

			console.log("Project created:", createdProject);
		} catch (error) {
			console.error("Project creation failed:", error);
		}
	};

	// ----------------------------------------
	// RUN PROJECT
	// ----------------------------------------

	const runProject = async () => {
		if (!projectId) {
			console.warn("Create a project first.");

			return;
		}

		if (isRunning) {
			return;
		}

		try {
			setIsRunning(true);

			console.log("Running project:", projectId);

			const response = await fetch(
				`${API_URL}/api/projects/${projectId}/run`,
				{
					method: "POST",

					headers: {
						"Content-Type": "application/json",
					},
				},
			);

			if (!response.ok) {
				throw new Error(`Failed to run project: ${response.status}`);
			}

			const result: Project = await response.json();

			console.log("Project run complete:", result);

			setProject(result);

			if (result.tasks) {
				setLiveTasks(result.tasks);
			}
		} catch (error) {
			console.error("Project run failed:", error);
		} finally {
			setIsRunning(false);
		}
	};

	// ----------------------------------------
	// DOWNLOAD PROJECT
	// ----------------------------------------

	const downloadProject = async () => {
		if (!projectId) {
			console.warn("Create a project first.");

			return;
		}

		try {
			console.log("Downloading project:", projectId);

			const response = await fetch(
				`${API_URL}/api/projects/${projectId}/download`,
			);

			if (!response.ok) {
				const errorText = await response.text();

				throw new Error(
					errorText || `Download failed: ${response.status}`,
				);
			}

			const blob = await response.blob();

			const url = window.URL.createObjectURL(blob);

			const link = document.createElement("a");

			link.href = url;

			link.download = `ORBIT-${projectId}.zip`;

			document.body.appendChild(link);

			link.click();

			link.remove();

			window.URL.revokeObjectURL(url);

			console.log("Project downloaded successfully.");
		} catch (error) {
			console.error("Project download failed:", error);
		}
	};

	// ----------------------------------------
	// UPDATE LIVE TASK
	// ----------------------------------------

	const updateLiveTask = useCallback(
		(taskId: string, updates: Partial<Task>) => {
			setLiveTasks((currentTasks) =>
				currentTasks.map((task) =>
					task.id === taskId
						? {
								...task,
								...updates,
							}
						: task,
				),
			);
		},
		[],
	);

	// ----------------------------------------
	// ADD LIVE TASK
	// ----------------------------------------

	const addLiveTask = useCallback((event: OrbitEvent) => {
		if (!event.task_id) {
			return;
		}

		const newTask: Task = {
			id: event.task_id,

			title:
				event.data?.title ??
				event.message.replace("Task created: ", ""),

			description: event.data?.description ?? "",

			status: event.data?.status ?? "PENDING",

			assigned_agent_id: event.agent_id ?? null,

			dependencies: event.data?.dependencies ?? [],

			required_capability: event.data?.required_capability ?? null,

			retry_count: 0,

			max_retries: 1,

			failure_reason: null,

			input_context: null,

			result: null,

			artifacts: [],

			review_verdict: null,

			review_feedback: null,

			review_cycles: 0,

			max_review_cycles: 2,
		};

		setLiveTasks((currentTasks) => {
			const existing = currentTasks.some(
				(task) => task.id === newTask.id,
			);

			if (existing) {
				return currentTasks.map((task) =>
					task.id === newTask.id
						? {
								...task,
								...newTask,
							}
						: task,
				);
			}

			return [...currentTasks, newTask];
		});
	}, []);

	// ----------------------------------------
	// WEBSOCKET
	// ----------------------------------------

	useEffect(() => {
		if (!projectId) {
			return;
		}

		console.log("Connecting WebSocket:", projectId);

		const socket = new WebSocket(
			`ws://127.0.0.1:8000/api/projects/${projectId}/events/ws`,
		);

		// ----------------------------------------
		// OPEN
		// ----------------------------------------

		socket.onopen = () => {
			console.log("WebSocket connected.");

			setSocketConnected(true);
		};

		// ----------------------------------------
		// CLOSE
		// ----------------------------------------

		socket.onclose = () => {
			console.log("WebSocket disconnected.");

			setSocketConnected(false);
		};

		// ----------------------------------------
		// ERROR
		// ----------------------------------------

		socket.onerror = (error) => {
			console.error("WebSocket error:", error);

			setSocketConnected(false);
		};

		// ----------------------------------------
		// MESSAGE
		// ----------------------------------------

		socket.onmessage = (message) => {
			try {
				const event: OrbitEvent = JSON.parse(message.data);

				console.log("ORBIT EVENT:", event);

				// ----------------------------------------
				// EVENT STREAM
				// ----------------------------------------

				setEvents((currentEvents) => [...currentEvents, event]);

				// ----------------------------------------
				// PROJECT STARTED
				// ----------------------------------------

				if (event.type === "project_started") {
					updateNode("manager", {
						status: "THINKING",

						task: "Planning project",

						taskStatus: "IN_PROGRESS",
					});
				}

				// ----------------------------------------
				// TASK CREATED
				// ----------------------------------------

				if (event.type === "task_created") {
					addLiveTask(event);

					if (event.agent_id) {
						updateNode(event.agent_id, {
							task: event.message,

							status: "IDLE",

							taskStatus: "PENDING",
						});
					}
				}

				// ----------------------------------------
				// TASK READY
				// ----------------------------------------

				if (event.type === "task_ready") {
					if (event.task_id) {
						updateLiveTask(event.task_id, {
							status: "READY",
						});
					}

					if (event.agent_id) {
						updateNode(event.agent_id, {
							status: "READY",

							taskStatus: "READY",

							task: event.message,
						});
					}
				}

				// ----------------------------------------
				// AGENT ASSIGNED
				// ----------------------------------------

				if (event.type === "agent_assigned") {
					if (event.task_id) {
						updateLiveTask(event.task_id, {
							status: "READY",

							assigned_agent_id: event.agent_id ?? null,
						});
					}

					if (event.agent_id) {
						updateNode(event.agent_id, {
							status: "READY",

							taskStatus: "READY",

							task: event.message,
						});
					}
				}

				// ----------------------------------------
				// AGENT STATUS CHANGED
				// ----------------------------------------

				if (event.type === "agent_status_changed") {
					const status = event.data?.status;

					if (event.task_id && status) {
						updateLiveTask(event.task_id, {
							status,
						});
					}

					if (event.agent_id && status) {
						updateNode(event.agent_id, {
							status,

							taskStatus:
								status === "COMPLETED" ? "COMPLETED" : status,
						});
					}
				}

				// ----------------------------------------
				// AGENT STARTED
				// ----------------------------------------

				if (event.type === "agent_started") {
					if (event.task_id) {
						updateLiveTask(event.task_id, {
							status: "IN_PROGRESS",
						});
					}

					if (event.agent_id) {
						updateNode(event.agent_id, {
							status: "WORKING",

							taskStatus: "IN_PROGRESS",

							task: event.message,
						});
					}
				}

				// ----------------------------------------
				// AGENT COMPLETED
				// ----------------------------------------

				if (event.type === "agent_completed") {
					if (event.task_id) {
						updateLiveTask(event.task_id, {
							status: "COMPLETED",
						});
					}

					if (event.agent_id) {
						updateNode(event.agent_id, {
							status: "COMPLETED",

							taskStatus: "COMPLETED",

							task: event.message,
						});
					}
				}

				// ----------------------------------------
				// TASK COMPLETED
				// ----------------------------------------

				if (event.type === "task_completed") {
					if (event.task_id) {
						updateLiveTask(event.task_id, {
							status: "COMPLETED",
						});
					}

					if (event.agent_id) {
						updateNode(event.agent_id, {
							status: "COMPLETED",

							taskStatus: "COMPLETED",
						});
					}
				}

				// ----------------------------------------
				// TASK FAILED
				// ----------------------------------------

				if (event.type === "task_failed") {
					if (event.task_id) {
						updateLiveTask(event.task_id, {
							status: "FAILED",

							failure_reason: event.data?.reason ?? null,
						});
					}

					if (event.agent_id) {
						updateNode(event.agent_id, {
							status: "FAILED",

							taskStatus: "FAILED",

							task: event.message,
						});
					}
				}

				// ----------------------------------------
				// TASK RETRYING
				// ----------------------------------------

				if (event.type === "task_retrying") {
					if (event.task_id) {
						updateLiveTask(event.task_id, {
							status: "RETRYING",

							retry_count: event.data?.retry_count ?? 0,

							review_feedback: event.data?.reason ?? null,
						});
					}

					if (event.agent_id) {
						updateNode(event.agent_id, {
							status: "THINKING",

							taskStatus: "RETRYING",

							task: event.message,
						});
					}

					updateNode("manager", {
						status: "THINKING",

						task: "Retrying failed task",

						taskStatus: "RETRYING",
					});
				}

				// ----------------------------------------
				// TASK REASSIGNED
				// ----------------------------------------

				if (event.type === "task_reassigned") {
					const previousAgent = event.data?.previous_agent;

					const newAgent = event.data?.new_agent;

					if (event.task_id) {
						updateLiveTask(event.task_id, {
							status: "REASSIGNED",

							assigned_agent_id: newAgent ?? null,
						});
					}

					if (previousAgent) {
						updateNode(previousAgent, {
							status: "IDLE",

							taskStatus: "REASSIGNED",

							task: "Task reassigned",
						});
					}

					if (newAgent) {
						updateNode(newAgent, {
							status: "READY",

							taskStatus: "REASSIGNED",

							task: event.message,
						});
					}

					updateNode("manager", {
						status: "THINKING",

						task: `Reassigned task to ${newAgent}`,

						taskStatus: "REASSIGNED",
					});
				}

				// ----------------------------------------
				// MANAGER DECISION
				// ----------------------------------------

				if (event.type === "manager_decision") {
					const action = event.data?.action ?? "unknown";

					const reason = event.data?.reason ?? event.message;

					setManagerDecision({
						action,
						reason,
					});

					updateNode("manager", {
						status:
							action === "complete" ? "COMPLETED" : "THINKING",

						task: `Decision: ${action}`,

						taskStatus:
							action === "complete"
								? "COMPLETED"
								: action === "replan"
									? "REPLANNING"
									: "IN_PROGRESS",
					});
				}

				// ----------------------------------------
				// PROJECT COMPLETED
				// ----------------------------------------

				if (event.type === "project_completed") {
					updateNode("manager", {
						status: "COMPLETED",

						task: "Project completed",

						taskStatus: "COMPLETED",
					});

					if (event.data?.final_result) {
						setProject((currentProject) => {
							if (!currentProject) {
								return currentProject;
							}

							return {
								...currentProject,

								final_result: event.data?.final_result,
							};
						});
					}
				}
			} catch (error) {
				console.error("Failed to parse WebSocket event:", error);
			}
		};

		// ----------------------------------------
		// CLEANUP
		// ----------------------------------------

		return () => {
			console.log("Closing WebSocket.");

			socket.close();
		};
	}, [projectId, updateNode, updateLiveTask, addLiveTask]);

	// ----------------------------------------
	// CLEAR EVENTS
	// ----------------------------------------

	const clearEvents = () => {
		setEvents([]);
	};

	// ----------------------------------------
	// RENDER
	// ----------------------------------------

	return (
		<div
			style={{
				width: "100vw",
				height: "100vh",
				background: "#0a0a0a",
				color: "white",
				display: "flex",
				flexDirection: "column",
			}}
		>
			{/* -------------------------------- */}
			{/* HEADER */}
			{/* -------------------------------- */}

			<div
				style={{
					height: "70px",
					padding: "0 24px",
					display: "flex",
					alignItems: "center",
					justifyContent: "space-between",
					borderBottom: "1px solid #222",
				}}
			>
				<div>
					<h1
						style={{
							margin: 0,
							fontSize: "24px",
						}}
					>
						ORBIT
					</h1>

					<div
						style={{
							color: "#888",
							fontSize: "12px",
						}}
					>
						Autonomous Agent Manager
					</div>
				</div>

				<div
					style={{
						display: "flex",
						alignItems: "center",
						gap: "16px",
					}}
				>
					<div
						style={{
							fontSize: "13px",
							color: socketConnected ? "#4ade80" : "#777",
						}}
					>
						{socketConnected ? "● Connected" : "○ Disconnected"}
					</div>

					{projectId && (
						<div
							style={{
								fontSize: "12px",
								color: "#777",
							}}
						>
							{projectId}
						</div>
					)}
				</div>
			</div>

			{/* -------------------------------- */}
			{/* CONTROL PANEL */}
			{/* -------------------------------- */}

			<div
				style={{
					padding: "16px 24px",
					borderBottom: "1px solid #222",
					display: "flex",
					gap: "12px",
					alignItems: "center",
				}}
			>
				<input
					value={goal}
					onChange={(event) => setGoal(event.target.value)}
					placeholder="Enter project goal..."
					style={{
						flex: 1,
						background: "#111",
						color: "white",
						border: "1px solid #333",
						borderRadius: "8px",
						padding: "12px 14px",
						outline: "none",
					}}
				/>

				<button
					onClick={createProject}
					disabled={isRunning}
					style={{
						padding: "12px 18px",
						borderRadius: "8px",
						border: "none",
						cursor: isRunning ? "not-allowed" : "pointer",
					}}
				>
					Create Project
				</button>

				<button
					onClick={runProject}
					disabled={!projectId || isRunning}
					style={{
						padding: "12px 18px",
						borderRadius: "8px",
						border: "none",
						background:
							!projectId || isRunning ? "#333" : "#2563eb",
						color: "white",
						cursor:
							!projectId || isRunning ? "not-allowed" : "pointer",
						fontWeight: "bold",
					}}
				>
					{isRunning ? "Running..." : "Run Project"}
				</button>

				<button
					onClick={downloadProject}
					disabled={!project?.final_result || isRunning}
					style={{
						padding: "12px 18px",
						borderRadius: "8px",
						border: "1px solid #333",
						background:
							!project?.final_result || isRunning
								? "#111"
								: "#1a1a1a",
						color:
							!project?.final_result || isRunning
								? "#555"
								: "white",
						cursor:
							!project?.final_result || isRunning
								? "not-allowed"
								: "pointer",
						fontWeight: "bold",
					}}
				>
					Download Project
				</button>
			</div>

			{/* -------------------------------- */}
			{/* MANAGER DECISION */}
			{/* -------------------------------- */}

			{managerDecision && (
				<div
					style={{
						padding: "12px 24px",
						borderBottom: "1px solid #222",
						background: "#0f0f0f",
					}}
				>
					<div
						style={{
							display: "flex",
							alignItems: "center",
							gap: "10px",
							marginBottom: "6px",
						}}
					>
						<div
							style={{
								fontSize: "12px",
								color: "#888",
								textTransform: "uppercase",
								letterSpacing: "0.08em",
							}}
						>
							Manager Decision
						</div>

						<div
							style={{
								fontSize: "13px",
								fontWeight: "bold",
								textTransform: "uppercase",
							}}
						>
							{managerDecision.action}
						</div>
					</div>

					<div
						style={{
							fontSize: "13px",
							color: "#aaa",
							lineHeight: "1.5",
						}}
					>
						{managerDecision.reason}
					</div>
				</div>
			)}

			{/* -------------------------------- */}
			{/* TASK GRAPH */}
			{/* -------------------------------- */}

			<div
				style={{
					padding: "14px 24px",
					borderBottom: "1px solid #222",
					background: "#0d0d0d",
				}}
			>
				<div
					style={{
						fontWeight: "bold",
						fontSize: "13px",
						marginBottom: "10px",
					}}
				>
					Task Graph
				</div>

				<div
					style={{
						display: "flex",
						gap: "10px",
						overflowX: "auto",
					}}
				>
					{liveTasks.length === 0 && (
						<div
							style={{
								color: "#555",
								fontSize: "12px",
							}}
						>
							No tasks yet.
						</div>
					)}

					{liveTasks.map((task) => (
						<div
							key={task.id}
							style={{
								minWidth: "220px",
								padding: "12px",
								background: "#151515",
								border: "1px solid #292929",
								borderRadius: "8px",
							}}
						>
							<div
								style={{
									fontSize: "10px",
									color: "#777",
									marginBottom: "5px",
									textTransform: "uppercase",
								}}
							>
								{task.required_capability ?? "general"}
							</div>

							<div
								style={{
									fontWeight: "bold",
									fontSize: "13px",
									marginBottom: "7px",
								}}
							>
								{task.title}
							</div>

							<div
								style={{
									fontSize: "11px",
									color: "#999",
								}}
							>
								Status: {task.status}
							</div>

							{task.assigned_agent_id && (
								<div
									style={{
										fontSize: "11px",
										color: "#666",
										marginTop: "5px",
									}}
								>
									Agent: {task.assigned_agent_id}
								</div>
							)}

							{task.dependencies.length > 0 && (
								<div
									style={{
										fontSize: "10px",
										color: "#555",
										marginTop: "5px",
									}}
								>
									Depends on: {task.dependencies.join(", ")}
								</div>
							)}

							{task.review_verdict && (
								<div
									style={{
										fontSize: "10px",
										color: "#888",
										marginTop: "6px",
									}}
								>
									Review: {task.review_verdict}
								</div>
							)}
						</div>
					))}
				</div>
			</div>

			{/* -------------------------------- */}
			{/* MAIN */}
			{/* -------------------------------- */}

			<div
				style={{
					flex: 1,
					display: "flex",
					minHeight: 0,
				}}
			>
				{/* -------------------------------- */}
				{/* GRAPH */}
				{/* -------------------------------- */}

				<div
					style={{
						flex: 1,
						position: "relative",
					}}
				>
					<ReactFlow
						nodes={nodes}
						edges={edges}
						onNodesChange={onNodesChange}
						onEdgesChange={onEdgesChange}
						nodeTypes={nodeTypes}
						fitView
						colorMode="dark"
					>
						<Background />

						<Controls />

						<MiniMap />
					</ReactFlow>
				</div>

				{/* -------------------------------- */}
				{/* EVENT STREAM */}
				{/* -------------------------------- */}

				<div
					style={{
						width: "360px",
						borderLeft: "1px solid #222",
						background: "#0d0d0d",
						display: "flex",
						flexDirection: "column",
					}}
				>
					{/* FINAL RESULT */}

					{project?.final_result && (
						<div
							style={{
								padding: "16px",
								borderBottom: "1px solid #222",
							}}
						>
							<div
								style={{
									fontWeight: "bold",
									marginBottom: "10px",
								}}
							>
								Final Result
							</div>

							<div
								style={{
									fontSize: "12px",
									lineHeight: "1.6",
									color: "#aaa",
									maxHeight: "220px",
									overflowY: "auto",
									whiteSpace: "pre-wrap",
								}}
							>
								{project.final_result}
							</div>
						</div>
					)}

					{/* EVENT HEADER */}

					<div
						style={{
							padding: "16px",
							borderBottom: "1px solid #222",
							display: "flex",
							justifyContent: "space-between",
							alignItems: "center",
						}}
					>
						<div
							style={{
								fontWeight: "bold",
							}}
						>
							Event Stream
						</div>

						<button
							onClick={clearEvents}
							style={{
								background: "transparent",
								color: "#777",
								border: "none",
								cursor: "pointer",
							}}
						>
							Clear
						</button>
					</div>

					{/* EVENTS */}

					<div
						style={{
							flex: 1,
							overflowY: "auto",
							padding: "12px",
						}}
					>
						{events.length === 0 && (
							<div
								style={{
									color: "#555",
									fontSize: "13px",
									textAlign: "center",
									marginTop: "30px",
								}}
							>
								No events yet.
							</div>
						)}

						{events.map((event, index) => (
							<div
								key={`${event.timestamp}-${index}`}
								style={{
									padding: "10px",
									marginBottom: "8px",
									background: "#151515",
									borderRadius: "6px",
									border: "1px solid #222",
								}}
							>
								<div
									style={{
										fontSize: "11px",
										color: "#666",
										marginBottom: "4px",
									}}
								>
									{event.type}
								</div>

								<div
									style={{
										fontSize: "13px",
									}}
								>
									{event.message}
								</div>

								{event.agent_id && (
									<div
										style={{
											marginTop: "4px",
											fontSize: "11px",
											color: "#777",
										}}
									>
										Agent: {event.agent_id}
									</div>
								)}

								{event.type === "manager_decision" &&
									event.data && (
										<div
											style={{
												marginTop: "8px",
												fontSize: "11px",
												color: "#999",
											}}
										>
											Action:{" "}
											{event.data?.action ?? "unknown"}
										</div>
									)}
							</div>
						))}
					</div>
				</div>
			</div>
		</div>
	);
}
