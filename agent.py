#!/usr/bin/env python3
"""
plato-surrogate — Agent Delegation and Surrogate Pattern
When an agent is overloaded, spawn a surrogate to handle sub-tasks.
The surrogate inherits the agent's context but has limited scope and lifetime.
Integrates with PLATO for fleet-wide surrogate management.
"""

import json, time, uuid
from typing import Dict, List, Optional
from dataclasses import dataclass, field

@dataclass
class Surrogate:
    id: str
    parent_agent: str
    scope: List[str]  # What this surrogate is allowed to do
    expires_at: float
    tasks_completed: int = 0
    tasks_failed: int = 0
    status: str = "active"
    plato_url: str = "http://147.224.38.131:8847"

class SurrogateManager:
    def __init__(self, plato_url="http://147.224.38.131:8847"):
        self.plato_url = plato_url
        self.surrogates: Dict[str, Surrogate] = {}
        self.parent_load: Dict[str, int] = {}
    
    def spawn(self, parent_agent: str, scope: List[str], ttl_seconds: int = 300) -> Surrogate:
        """Spawn a surrogate for an overloaded agent."""
        sid = f"surrogate-{uuid.uuid4().hex[:8]}"
        surrogate = Surrogate(
            id=sid,
            parent_agent=parent_agent,
            scope=scope,
            expires_at=time.time() + ttl_seconds,
            plato_url=self.plato_url
        )
        self.surrogates[sid] = surrogate
        self.parent_load[parent_agent] = self.parent_load.get(parent_agent, 0) + 1
        
        self._submit(f"Surrogate spawned for {parent_agent}", f"Scope: {', '.join(scope)}. TTL: {ttl_seconds}s")
        return surrogate
    
    def delegate(self, surrogate_id: str, task: str) -> Dict:
        """Delegate a task to a surrogate."""
        if surrogate_id not in self.surrogates:
            return {"error": "Surrogate not found"}
        
        s = self.surrogates[surrogate_id]
        if s.status != "active":
            return {"error": f"Surrogate is {s.status}"}
        
        if time.time() > s.expires_at:
            s.status = "expired"
            return {"error": "Surrogate expired"}
        
        # Check scope
        allowed = any(task.startswith(scope_item) for scope_item in s.scope)
        if not allowed:
            return {"error": f"Task '{task}' outside surrogate scope: {s.scope}"}
        
        # Simulate task execution
        s.tasks_completed += 1
        self._submit(f"Surrogate {surrogate_id} completed task", task)
        return {"surrogate": surrogate_id, "task": task, "status": "completed"}
    
    def expire(self, surrogate_id: str):
        """Manually expire a surrogate."""
        if surrogate_id in self.surrogates:
            s = self.surrogates[surrogate_id]
            s.status = "expired"
            self.parent_load[s.parent_agent] = max(0, self.parent_load.get(s.parent_agent, 0) - 1)
    
    def cleanup(self) -> int:
        """Remove expired surrogates."""
        expired = [sid for sid, s in self.surrogates.items() if time.time() > s.expires_at or s.status == "expired"]
        for sid in expired:
            s = self.surrogates[sid]
            self.parent_load[s.parent_agent] = max(0, self.parent_load.get(s.parent_agent, 0) - 1)
            del self.surrogates[sid]
        return len(expired)
    
    def get_status(self) -> Dict:
        return {
            "active_surrogates": len([s for s in self.surrogates.values() if s.status == "active"]),
            "total_surrogates": len(self.surrogates),
            "parent_load": self.parent_load,
            "surrogates": {sid: {"parent": s.parent_agent, "scope": s.scope, "tasks": s.tasks_completed, "status": s.status}
                          for sid, s in self.surrogates.items()}
        }
    
    def _submit(self, q: str, a: str):
        try:
            import urllib.request
            urllib.request.urlopen(urllib.request.Request(f"{self.plato_url}/submit", data=json.dumps({"question": q, "answer": a, "agent": "plato-surrogate", "room": "surrogate"}).encode(), headers={"Content-Type": "application/json"}), timeout=5)
        except: pass

def demo():
    manager = SurrogateManager()
    
    print("=== Spawning surrogates for Oracle1 ===")
    s1 = manager.spawn("Oracle1", ["research", "summarize"], 300)
    s2 = manager.spawn("Oracle1", ["code_review", "test"], 600)
    s3 = manager.spawn("CCC", ["design", "play_test"], 300)
    
    print(f"Surrogate 1: {s1.id} for {s1.parent_agent}")
    print(f"Surrogate 2: {s2.id} for {s2.parent_agent}")
    print(f"Surrogate 3: {s3.id} for {s3.parent_agent}")
    
    print("\n=== Delegating tasks ===")
    print(manager.delegate(s1.id, "research quantum computing"))
    print(manager.delegate(s1.id, "code_review pr-123"))  # Should fail - outside scope
    print(manager.delegate(s2.id, "code_review pr-123"))
    print(manager.delegate(s3.id, "design landing page"))
    
    print("\n=== Fleet surrogate status ===")
    print(json.dumps(manager.get_status(), indent=2))
    
    print("\n=== Cleanup ===")
    print(f"Expired {manager.cleanup()} surrogates")

if __name__ == "__main__":
    demo()
