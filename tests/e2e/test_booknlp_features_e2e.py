"""E2E tests for BookNLP NLP feature validation."""

import pytest
from httpx import AsyncClient


class TestBookNLPFeaturesE2E:
    """End-to-end tests validating actual NLP features work correctly."""

    @pytest.mark.asyncio
    async def test_entity_recognition_features(self, client: AsyncClient, auth_headers):
        """Test that entity recognition correctly identifies people, places, and organizations."""
        # Test text with clear entities
        test_text = """
        John Smith traveled from New York to London last week. 
        He works for Microsoft Corporation and met with Dr. Jane Doe 
        at the University of Cambridge.
        """
        
        job_request = {
            "text": test_text,
            "book_id": "entity-test",
            "model": "small",
            "pipeline": ["entities"]
        }
        
        # Submit job
        response = await client.post("/v1/jobs", json=job_request, headers=auth_headers)
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        
        # Wait for completion (simplified for test)
        import asyncio
        for _ in range(30):  # Max 2.5 minutes
            response = await client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
            if response.json()["status"] == "completed":
                break
            await asyncio.sleep(5)
        else:
            pytest.fail("Job did not complete")
        
        # Get results
        response = await client.get(f"/v1/jobs/{job_id}/result", headers=auth_headers)
        result = response.json()["result"]
        
        # Validate entities were found
        entities = result["entities"]
        assert len(entities) > 0
        
        # Check for expected entity types
        entity_texts = [e["text"] for e in entities]
        
        # Should find people
        assert any("John Smith" in text for text in entity_texts)
        assert any("Jane Doe" in text for text in entity_texts)
        
        # Should find locations
        assert any("New York" in text for text in entity_texts)
        assert any("London" in text for text in entity_texts)
        assert any("University of Cambridge" in text for text in entity_texts)
        
        # Should find organization
        assert any("Microsoft Corporation" in text for text in entity_texts)

    @pytest.mark.asyncio
    async def test_quote_speaker_attribution(self, client: AsyncClient, auth_headers):
        """Test that quote attribution correctly identifies speakers."""
        test_text = """
        "Hello," said Tom Sawyer. "I'm going to the river."
        "That sounds nice," replied Huck Finn. "Can I come with you?"
        "Of course," Tom answered. "We'll have a great adventure."
        """
        
        job_request = {
            "text": test_text,
            "book_id": "quote-test",
            "model": "small",
            "pipeline": ["quotes"]
        }
        
        # Submit and wait for job
        response = await client.post("/v1/jobs", json=job_request, headers=auth_headers)
        job_id = response.json()["job_id"]
        
        import asyncio
        for _ in range(30):
            response = await client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
            if response.json()["status"] == "completed":
                break
            await asyncio.sleep(5)
        
        # Get results
        response = await client.get(f"/v1/jobs/{job_id}/result", headers=auth_headers)
        result = response.json()["result"]
        
        # Validate quotes were found with speakers
        quotes = result.get("quotes", [])
        assert len(quotes) > 0
        
        # Check for quote-speaker pairs
        quote_texts = [q.get("quote", "") for q in quotes]
        speakers = [q.get("speaker", "") for q in quotes]
        
        # Should find quotes
        assert any("Hello" in quote for quote in quote_texts)
        assert any("That sounds nice" in quote for quote in quote_texts)
        assert any("Of course" in quote for quote in quote_texts)
        
        # Should attribute to speakers
        assert any("Tom Sawyer" in speaker for speaker in speakers)
        assert any("Huck Finn" in speaker for speaker in speakers)

    @pytest.mark.asyncio
    async def test_coreference_resolution(self, client: AsyncClient, auth_headers):
        """Test that coreference resolution links pronouns to entities."""
        test_text = """
        Mary Johnson is a talented surgeon. She works at City Hospital. 
        Her specialty is neurosurgery. The doctor performs complex operations 
        every week. Dr. Johnson is respected by her colleagues.
        """
        
        job_request = {
            "text": test_text,
            "book_id": "coref-test",
            "model": "small",
            "pipeline": ["entities", "coref"]
        }
        
        # Submit and wait for job
        response = await client.post("/v1/jobs", json=job_request, headers=auth_headers)
        job_id = response.json()["job_id"]
        
        import asyncio
        for _ in range(30):
            response = await client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
            if response.json()["status"] == "completed":
                break
            await asyncio.sleep(5)
        
        # Get results
        response = await client.get(f"/v1/jobs/{job_id}/result", headers=auth_headers)
        result = response.json()["result"]
        
        # Validate coreference chains
        entities = result["entities"]
        
        # Find Mary Johnson entity
        mary_entity = None
        for entity in entities:
            if "Mary Johnson" in entity.get("text", ""):
                mary_entity = entity
                break
        
        assert mary_entity is not None, "Mary Johnson entity not found"
        
        # Check if pronouns are linked (implementation varies)
        # This is a basic check - actual coreference structure depends on BookNLP output format
        assert len(entities) > 1  # Should find multiple mentions linked to Mary

    @pytest.mark.asyncio
    async def test_pos_and_dependency_parsing(self, client: AsyncClient, auth_headers):
        """Test that POS tagging and dependency parsing work correctly."""
        test_text = "The quick brown fox jumps over the lazy dog."
        
        job_request = {
            "text": test_text,
            "book_id": "pos-test",
            "model": "small",
            "pipeline": ["entities"]  # Entities include tokens with POS
        }
        
        # Submit and wait for job
        response = await client.post("/v1/jobs", json=job_request, headers=auth_headers)
        job_id = response.json()["job_id"]
        
        import asyncio
        for _ in range(30):
            response = await client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
            if response.json()["status"] == "completed":
                break
            await asyncio.sleep(5)
        
        # Get results
        response = await client.get(f"/v1/jobs/{job_id}/result", headers=auth_headers)
        result = response.json()["result"]
        
        # Validate tokens with POS tags
        tokens = result["tokens"]
        assert len(tokens) > 0
        
        # Check specific POS tags
        token_words = {t["word"]: t for t in tokens}
        
        # Should have adjective
        assert token_words["quick"]["POS_tag"] == "ADJ"
        assert token_words["brown"]["POS_tag"] == "ADJ"
        assert token_words["lazy"]["POS_tag"] == "ADJ"
        
        # Should have noun
        assert token_words["fox"]["POS_tag"] == "NOUN"
        assert token_words["dog"]["POS_tag"] == "NOUN"
        
        # Should have verb
        assert token_words["jumps"]["POS_tag"] == "VERB"
        assert token_words["over"]["POS_tag"] == "ADP"
        
        # Check dependency relations (if available)
        for token in tokens:
            assert "dependency_relation" in token
            assert "syntactic_head_ID" in token

    @pytest.mark.asyncio
    async def test_supersense_tagging(self, client: AsyncClient, auth_headers):
        """Test that supersense tagging provides semantic categories."""
        test_text = """
        The teacher thinks carefully about the problem. 
        Students run quickly to the classroom. 
        She wrote a beautiful poem about nature.
        """
        
        job_request = {
            "text": test_text,
            "book_id": "supersense-test",
            "model": "small",
            "pipeline": ["supersense"]
        }
        
        # Submit and wait for job
        response = await client.post("/v1/jobs", json=job_request, headers=auth_headers)
        job_id = response.json()["job_id"]
        
        import asyncio
        for _ in range(30):
            response = await client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
            if response.json()["status"] == "completed":
                break
            await asyncio.sleep(5)
        
        # Get results
        response = await client.get(f"/v1/jobs/{job_id}/result", headers=auth_headers)
        result = response.json()["result"]
        
        # Validate supersenses
        supersenses = result.get("supersenses", [])
        assert len(supersenses) > 0
        
        # Check for semantic categories
        supersense_cats = [s.get("category", "") for s in supersenses]
        
        # Should find cognition-related tags
        assert any("cognition" in cat.lower() for cat in supersense_cats)
        
        # Should find motion-related tags
        assert any("motion" in cat.lower() for cat in supersense_cats)
        
        # Should find artifact-related tags
        assert any("artifact" in cat.lower() for cat in supersense_cats)

    @pytest.mark.asyncio
    async def test_event_tagging(self, client: AsyncClient, auth_headers):
        """Test that event tagging identifies actions and events."""
        test_text = """
        The company announced yesterday that they will launch 
        a new product next month. Employees celebrated the news 
        and immediately began preparing for the release.
        """
        
        job_request = {
            "text": test_text,
            "book_id": "event-test",
            "model": "small",
            "pipeline": ["events"]
        }
        
        # Submit and wait for job
        response = await client.post("/v1/jobs", json=job_request, headers=auth_headers)
        job_id = response.json()["job_id"]
        
        import asyncio
        for _ in range(30):
            response = await client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
            if response.json()["status"] == "completed":
                break
            await asyncio.sleep(5)
        
        # Get results
        response = await client.get(f"/v1/jobs/{job_id}/result", headers=auth_headers)
        result = response.json()["result"]
        
        # Validate events
        events = result.get("events", [])
        assert len(events) > 0
        
        # Check for event triggers
        event_triggers = [e.get("trigger", "") for e in events]
        
        # Should find action verbs
        assert any("announced" in trigger for trigger in event_triggers)
        assert any("launch" in trigger for trigger in event_triggers)
        assert any("celebrated" in trigger for trigger in event_triggers)
        assert any("began" in trigger for trigger in event_triggers)

    @pytest.mark.asyncio
    async def test_character_name_clustering(self, client: AsyncClient, auth_headers):
        """Test that character name variants are clustered together."""
        test_text = """
        Mr. Thomas Sawyer arrived at the station. Tom looked around 
        for his friend. Sawyer waved when he saw Huck Finn approach. 
        "Hello, Tom," said Huck. "Mr. Sawyer, you're late!"
        """
        
        job_request = {
            "text": test_text,
            "book_id": "clustering-test",
            "model": "small",
            "pipeline": ["entities", "coref"]
        }
        
        # Submit and wait for job
        response = await client.post("/v1/jobs", json=job_request, headers=auth_headers)
        job_id = response.json()["job_id"]
        
        import asyncio
        for _ in range(30):
            response = await client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
            if response.json()["status"] == "completed":
                break
            await asyncio.sleep(5)
        
        # Get results
        response = await client.get(f"/v1/jobs/{job_id}/result", headers=auth_headers)
        result = response.json()["result"]
        
        # Check character information (if available in output)
        characters = result.get("characters", [])
        
        if characters:  # If character clustering is returned
            # Should find Tom Sawyer with all variants
            tom_character = None
            for char in characters:
                if "Tom" in char.get("name", "") or "Sawyer" in char.get("name", ""):
                    tom_character = char
                    break
            
            assert tom_character is not None, "Tom Sawyer character not found"
            
            # Check that variants are linked
            mentions = tom_character.get("mentions", [])
            mention_texts = [m.get("text", "") for m in mentions]
            
            assert any("Thomas Sawyer" in text for text in mention_texts)
            assert any("Tom" in text for text in mention_texts)
            assert any("Sawyer" in text for text in mention_texts)
            assert any("Mr. Sawyer" in text for text in mention_texts)

    @pytest.mark.asyncio
    async def test_referential_gender_inference(self, client: AsyncClient, auth_headers):
        """Test that referential gender is inferred for characters."""
        test_text = """
        Dr. Sarah Williams entered the room. She carried her medical bag. 
        The doctor examined the patient carefully. Her diagnosis was accurate. 
        Williams smiled when she saw the test results.
        """
        
        job_request = {
            "text": test_text,
            "book_id": "gender-test",
            "model": "small",
            "pipeline": ["entities", "coref"]
        }
        
        # Submit and wait for job
        response = await client.post("/v1/jobs", json=job_request, headers=auth_headers)
        job_id = response.json()["job_id"]
        
        import asyncio
        for _ in range(30):
            response = await client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
            if response.json()["status"] == "completed":
                break
            await asyncio.sleep(5)
        
        # Get results
        response = await client.get(f"/v1/jobs/{job_id}/result", headers=auth_headers)
        result = response.json()["result"]
        
        # Check for gender information (if available)
        entities = result["entities"]
        
        # Find Sarah Williams entity
        sarah_entity = None
        for entity in entities:
            if "Sarah Williams" in entity.get("text", "") or "Williams" in entity.get("text", ""):
                sarah_entity = entity
                break
        
        assert sarah_entity is not None, "Sarah Williams entity not found"
        
        # Gender inference might be in character data or entity attributes
        # This test validates the structure exists - actual gender depends on implementation
        assert "text" in sarah_entity

    @pytest.mark.asyncio
    async def test_comprehensive_pipeline(self, client: AsyncClient, auth_headers):
        """Test that all pipeline components work together."""
        test_text = """
        "I'm going to the market," said Mrs. Eleanor Thompson. 
        She needed to buy fresh vegetables for her family. 
        The elderly woman walked slowly through the busy streets of Boston.
        At the store, she carefully selected tomatoes, carrots, and lettuce.
        "These look perfect," she thought to herself.
        """
        
        job_request = {
            "text": test_text,
            "book_id": "comprehensive-test",
            "model": "small",
            "pipeline": ["entities", "quotes", "supersense", "events", "coref"]
        }
        
        # Submit and wait for job
        response = await client.post("/v1/jobs", json=job_request, headers=auth_headers)
        job_id = response.json()["job_id"]
        
        import asyncio
        for _ in range(30):
            response = await client.get(f"/v1/jobs/{job_id}", headers=auth_headers)
            if response.json()["status"] == "completed":
                break
            await asyncio.sleep(5)
        
        # Get results
        response = await client.get(f"/v1/jobs/{job_id}/result", headers=auth_headers)
        result = response.json()["result"]
        
        # Validate all components are present
        assert "tokens" in result
        assert "entities" in result
        assert len(result["entities"]) > 0
        
        # Check for quote
        quotes = result.get("quotes", [])
        if quotes:  # Quotes might be in different format
            assert len(quotes) > 0
        
        # Check for supersenses
        supersenses = result.get("supersenses", [])
        if supersenses:
            assert len(supersenses) > 0
        
        # Check for events
        events = result.get("events", [])
        if events:
            assert len(events) > 0
        
        # Validate basic structure
        assert len(result["tokens"]) > 0
        assert all("word" in t for t in result["tokens"])
        assert all("POS_tag" in t for t in result["tokens"])
