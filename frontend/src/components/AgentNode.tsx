import { Handle, Position } from "@xyflow/react";

import type { NodeProps, Node } from "@xyflow/react";

type AgentNodeData = {
    name: string;
    icon: string;
    role: string;
    task: string;
    status: string;
    taskStatus: string;
};

type AgentNodeType = Node<AgentNodeData, "agent">;

export default function AgentNode({ data }: NodeProps<AgentNodeType>) {
    console.log(
        "RENDERING NODE:",
        data.name,
        "STATUS:",
        data.status,
        "TASK:",
        data.taskStatus,
    );

    let background = "#374151";

    if (data.status === "READY") {
        background = "#ca8a04";
    }

    if (data.status === "THINKING") {
        background = "#9333ea";
    }

    if (data.status === "WORKING") {
        background = "#2563eb";
    }

    if (data.status === "COMPLETED") {
        background = "#16a34a";
    }

    if (data.status === "FAILED") {
        background = "#dc2626";
    }

    if (data.taskStatus === "REASSIGNED") {
        background = "#ea580c";
    }

    return (
        <div
            style={{
                border: "2px solid #555",
                borderRadius: "12px",
                padding: "16px",
                width: "220px",
                background: "#111",
                color: "white",
                position: "relative",
            }}
        >
            <Handle type="target" position={Position.Left} id="target" />

            <div
                style={{
                    fontSize: "18px",
                    fontWeight: "bold",
                }}
            >
                {data.icon} {data.name}
            </div>

            <div
                style={{
                    marginTop: "8px",
                    fontSize: "13px",
                    color: "#aaa",
                }}
            >
                {data.role}
            </div>

            <div
                style={{
                    marginTop: "12px",
                    fontSize: "15px",
                }}
            >
                {data.task}
            </div>

            <div
                style={{
                    marginTop: "12px",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    background,
                    fontWeight: "bold",
                    display: "inline-block",
                }}
            >
                {data.status}
            </div>

            <div
                style={{
                    marginTop: "8px",
                    fontSize: "12px",
                    color: "#aaa",
                }}
            >
                Task: {data.taskStatus}
            </div>

            <Handle type="source" position={Position.Right} id="source" />
        </div>
    );
}
