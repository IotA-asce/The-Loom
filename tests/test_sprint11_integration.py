"""Integration tests for Sprint 11 API endpoints and WebSocket functionality."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.api import app


# Mark all tests as asyncio
pytestmark = pytest.mark.asyncio


class TestWriterEndpoints:
    """Test writer engine endpoints."""

    async def test_generate_text_endpoint(self, client):
        """Test POST /api/writer/generate returns valid response."""
        response = client.post(
            "/api/writer/generate",
            json={
                "nodeId": "test-node-1",
                "branchId": "main",
                "userPrompt": "Continue the story with a dramatic twist",
                "temperature": 0.7,
                "maxTokens": 500,
                "contextChunks": ["Context chunk 1", "Context chunk 2"],
                "styleExemplars": ["Style example 1"],
                "characterIds": ["char-1"],
                "tunerSettings": {"violence": 0.5, "humor": 0.3, "romance": 0.4},
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "jobId" in data
        assert "generatedText" in data
        assert "wordCount" in data
        assert "styleSimilarity" in data
        assert "contradictionRate" in data
        assert "promptVersion" in data
        assert data["wordCount"] > 0
        assert 0 <= data["styleSimilarity"] <= 1

    async def test_generate_text_missing_required_fields(self, client):
        """Test that missing required fields returns error."""
        response = client.post(
            "/api/writer/generate",
            json={
                "userPrompt": "Test prompt",
                # Missing nodeId and branchId
            },
        )
        
        # Should either succeed with defaults or fail validation
        assert response.status_code in [200, 422]

    async def test_get_style_exemplars_endpoint(self, client):
        """Test GET /api/writer/style-exemplars returns exemplars."""
        response = client.get(
            "/api/writer/style-exemplars",
            params={"query": "dramatic scene with tension", "topK": 3},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "exemplars" in data
        assert isinstance(data["exemplars"], list)
        
        if data["exemplars"]:
            exemplar = data["exemplars"][0]
            assert "id" in exemplar
            assert "text" in exemplar
            assert "similarity" in exemplar

    async def test_check_contradictions_endpoint(self, client):
        """Test POST /api/writer/check-contradictions detects contradictions."""
        response = client.post(
            "/api/writer/check-contradictions",
            json={
                "generatedText": "The character is dead. The character is alive.",
                "sourceContext": "The character died in the previous chapter.",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "contradictions" in data
        assert "contradictionRate" in data
        assert "suggestedFixes" in data
        assert isinstance(data["contradictions"], list)
        assert isinstance(data["suggestedFixes"], list)


class TestArtistEndpoints:
    """Test artist engine endpoints."""

    async def test_generate_panels_endpoint(self, client):
        """Test POST /api/artist/generate-panels returns valid response."""
        response = client.post(
            "/api/artist/generate-panels",
            json={
                "nodeId": "test-node-1",
                "branchId": "main",
                "sceneBlueprint": {
                    "setting": "Dark forest at night",
                    "timeOfDay": "night",
                    "weather": "clear",
                    "shotType": "wide",
                    "cameraAngle": "eye_level",
                    "focusPoint": "Main character",
                    "props": ["lantern", "sword"],
                    "characters": [
                        {
                            "characterId": "char-1",
                            "position": "center",
                            "pose": "standing alert",
                            "expression": "determined",
                        }
                    ],
                },
                "atmosphereSettings": {
                    "presetId": "dark",
                    "direction": "top",
                    "intensity": 0.8,
                    "contrast": 0.7,
                    "shadowHardness": 0.6,
                    "textureDetail": 0.7,
                    "textureStyle": "gritty",
                    "weathering": 0.4,
                },
                "panelCount": 4,
                "aspectRatio": "16:9",
                "cfgScale": 7.5,
                "steps": 28,
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "jobId" in data
        assert "panels" in data
        assert "overallQuality" in data
        assert "continuityScore" in data
        assert isinstance(data["panels"], list)
        
        if data["panels"]:
            panel = data["panels"][0]
            assert "panelId" in panel
            assert "index" in panel
            assert "status" in panel


class TestRetrievalEndpoints:
    """Test retrieval engine endpoints."""

    async def test_retrieve_context_endpoint(self, client):
        """Test POST /api/retrieve/context returns relevant chunks."""
        response = client.post(
            "/api/retrieve/context",
            json={
                "query": "character motivation and backstory",
                "branchId": "main",
                "limit": 5,
                "filters": {"type": "character", "importance": "high"},
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "chunks" in data
        assert "totalTokens" in data
        assert isinstance(data["chunks"], list)
        
        if data["chunks"]:
            chunk = data["chunks"][0]
            assert "id" in chunk
            assert "text" in chunk
            assert "source" in chunk
            assert "branchId" in chunk
            assert "relevanceScore" in chunk
            assert "tokenCount" in chunk


class TestSimulationEndpoints:
    """Test consequence simulation endpoints."""

    async def test_simulate_impact_endpoint(self, client):
        """Test POST /api/simulate/impact returns impact analysis."""
        response = client.post(
            "/api/simulate/impact",
            json={
                "nodeId": "node-123",
                "changeType": "edit",
                "description": "Change the character's decision to spare the villain",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "affectedNodes" in data
        assert "consistencyScore" in data
        assert "riskLevel" in data
        assert "estimatedTokens" in data
        assert "estimatedTime" in data
        assert "suggestedActions" in data
        
        assert isinstance(data["affectedNodes"], list)
        assert data["riskLevel"] in ["low", "medium", "high", "critical"]
        assert 0 <= data["consistencyScore"] <= 100
        
        if data["affectedNodes"]:
            node = data["affectedNodes"][0]
            assert "id" in node
            assert "name" in node
            assert "impact" in node
            assert "description" in node

    async def test_simulate_impact_delete(self, client):
        """Test simulate impact with delete change type."""
        response = client.post(
            "/api/simulate/impact",
            json={
                "nodeId": "node-123",
                "changeType": "delete",
                "description": "Remove this scene entirely",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["affectedNodes"]) >= 2  # Delete affects more nodes
        assert data["riskLevel"] in ["high", "critical"]

    async def test_simulate_impact_reorder(self, client):
        """Test simulate impact with reorder change type."""
        response = client.post(
            "/api/simulate/impact",
            json={
                "nodeId": "node-123",
                "changeType": "reorder",
                "description": "Move this scene earlier in the timeline",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["riskLevel"] in ["low", "medium"]


class TestWebSocketFunctionality:
    """Test WebSocket real-time updates."""

    async def test_websocket_connection(self, client):
        """Test WebSocket connection can be established."""
        # Note: FastAPI TestClient doesn't support WebSocket natively
        # This test documents the expected behavior
        pass

    async def test_websocket_ping_pong(self, client):
        """Test WebSocket ping/pong keepalive."""
        # WebSocket functionality tested manually or with async test client
        pass


class TestAsyncGenerationEndpoints:
    """Test async generation with WebSocket progress."""

    async def test_writer_generate_async(self, client):
        """Test POST /api/writer/generate-async starts async job."""
        response = client.post(
            "/api/writer/generate-async",
            json={
                "nodeId": "test-node-1",
                "branchId": "main",
                "userPrompt": "Generate async test",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "jobId" in data
        assert "status" in data
        assert data["status"] == "started"

    async def test_artist_generate_async(self, client):
        """Test POST /api/artist/generate-panels-async starts async job."""
        response = client.post(
            "/api/artist/generate-panels-async",
            json={
                "nodeId": "test-node-1",
                "branchId": "main",
                "sceneBlueprint": {"setting": "Test scene"},
                "atmosphereSettings": {"presetId": "neutral"},
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "jobId" in data
        assert "status" in data
        assert data["status"] == "started"


class TestEndpointIntegration:
    """Integration tests for complete workflows."""

    async def test_full_text_generation_workflow(self, client):
        """Test complete text generation workflow."""
        # 1. Retrieve context
        context_response = client.post(
            "/api/retrieve/context",
            json={"query": "story background", "branchId": "main", "limit": 3},
        )
        assert context_response.status_code == 200
        context_data = context_response.json()
        
        # 2. Get style exemplars
        exemplars_response = client.get(
            "/api/writer/style-exemplars",
            params={"query": "dramatic prose", "topK": 3},
        )
        assert exemplars_response.status_code == 200
        
        # 3. Generate text
        generate_response = client.post(
            "/api/writer/generate",
            json={
                "nodeId": "workflow-test",
                "branchId": "main",
                "userPrompt": "Continue with dramatic tension",
                "contextChunks": [c["text"] for c in context_data.get("chunks", [])],
                "temperature": 0.7,
            },
        )
        assert generate_response.status_code == 200
        gen_data = generate_response.json()
        
        # 4. Check contradictions
        check_response = client.post(
            "/api/writer/check-contradictions",
            json={
                "generatedText": gen_data["generatedText"],
                "sourceContext": " ".join([c["text"] for c in context_data.get("chunks", [])]),
            },
        )
        assert check_response.status_code == 200

    async def test_full_panel_generation_workflow(self, client):
        """Test complete panel generation workflow."""
        # 1. Retrieve context for scene
        context_response = client.post(
            "/api/retrieve/context",
            json={"query": "battle scene description", "branchId": "main", "limit": 3},
        )
        assert context_response.status_code == 200
        
        # 2. Generate panels
        panels_response = client.post(
            "/api/artist/generate-panels",
            json={
                "nodeId": "panel-workflow-test",
                "branchId": "main",
                "sceneBlueprint": {
                    "setting": "Battlefield at dawn",
                    "timeOfDay": "dawn",
                    "shotType": "wide",
                    "cameraAngle": "high",
                    "props": ["swords", "armor", "banners"],
                    "characters": [
                        {
                            "characterId": "hero",
                            "position": "center",
                            "pose": "fighting stance",
                            "expression": "determined",
                        }
                    ],
                },
                "atmosphereSettings": {
                    "presetId": "light",
                    "direction": "top",
                    "intensity": 0.7,
                },
                "panelCount": 4,
            },
        )
        assert panels_response.status_code == 200
        data = panels_response.json()
        assert len(data["panels"]) == 4


# Fixtures

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from fastapi.testclient import TestClient
    return TestClient(app)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
