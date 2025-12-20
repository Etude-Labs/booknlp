"""Fixtures for benchmark tests."""

import pytest


# Sample texts of varying sizes for benchmarking
SAMPLE_1K_TOKENS = """
The old mansion stood at the end of the lane, its windows dark and empty. Sarah walked slowly up the 
gravel path, her footsteps crunching in the evening silence. She had inherited this place from her 
grandmother, a woman she barely remembered. The lawyer had called it "a significant property" but 
looking at it now, Sarah could only see decay and neglect.

The front door creaked as she pushed it open. Inside, dust motes danced in the fading light that 
filtered through grimy windows. Furniture lay draped in white sheets, ghostly shapes in the gloom. 
Sarah pulled out her phone and turned on the flashlight, sweeping it across the entrance hall.

"Hello?" she called out, though she wasn't sure why. The house had been empty for years. Her voice 
echoed off the high ceilings and faded into silence.

She found the living room first, a grand space with a fireplace that dominated one wall. Above the 
mantle hung a portrait, and Sarah's breath caught when she saw it. The woman in the painting looked 
exactly like her. The same dark hair, the same green eyes, the same slight upturn at the corner of 
the mouth. It was like looking into a mirror that showed her dressed in Victorian clothing.

"Grandmother," Sarah whispered. She had seen photographs, of course, but this portrait captured 
something the old photos had missed. There was a spark in those painted eyes, a hint of secrets 
kept and stories untold.

The rest of the house revealed more mysteries. In the library, she found shelves of leather-bound 
journals, all written in her grandmother's careful hand. In the study, there was a locked desk 
drawer that rattled when she tried to open it. In the conservatory, dead plants in ornate pots 
stood like sentinels around a central fountain that had long since run dry.

But it was the basement that held the biggest surprise. Behind a hidden door, disguised as part of 
the wall paneling, Sarah found a room that shouldn't exist. The space was clean, unlike the rest 
of the house. Modern equipment hummed quietly in the corners. Computer screens glowed with data 
she couldn't understand.

"What were you doing down here, Grandmother?" Sarah asked the empty room.

A voice behind her made her spin around. "I was hoping you'd find this place."

The woman standing in the doorway looked exactly like the portrait upstairs, exactly like Sarah 
herself. But that was impossible. Her grandmother had died ten years ago.

"Don't be afraid," the woman said with a smile that Sarah recognized as her own. "I have so much 
to tell you, and we don't have much time. They'll be coming soon."

"Who?" Sarah managed to ask. "Who's coming?"

"The others," her grandmother said. "The ones who've been waiting for you to claim your inheritance. 
The real inheritance, not the house. You see, my dear, our family has been guarding something for 
generations. Something powerful. Something dangerous. And now it's your turn."

She held out her hand, and in her palm was a small golden key that seemed to glow with its own light.

"Are you ready to learn the truth about who you really are?"
""".strip()


@pytest.fixture
def sample_1k_text():
    """Return sample text with approximately 1K tokens."""
    return SAMPLE_1K_TOKENS


@pytest.fixture
def sample_10k_text(sample_1k_text):
    """Return sample text with approximately 10K tokens."""
    # Repeat the 1K sample 10 times with slight variations
    paragraphs = []
    for i in range(10):
        # Add chapter headers to make it more realistic
        paragraphs.append(f"\n\nChapter {i + 1}\n\n")
        paragraphs.append(sample_1k_text)
    return "".join(paragraphs)


@pytest.fixture
def benchmark_result_template():
    """Template for recording benchmark results."""
    return {
        "model": None,
        "device": None,
        "token_count": 0,
        "processing_time_ms": 0,
        "tokens_per_second": 0.0,
    }
