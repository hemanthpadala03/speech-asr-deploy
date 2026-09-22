from asrserve.agents.eval import _score_summary, load_fixture_transcripts, summarize_scores, PromptScore
from asrserve.agents.prompts.loader import list_versions, render_prompt


def test_render_prompt_v1_includes_transcript():
    out = render_prompt("meeting_summary_v1", transcript="hello there")
    assert "hello there" in out


def test_render_prompt_v2_has_rules_and_transcript():
    out = render_prompt("meeting_summary_v2", transcript="the client approved $2M")
    assert "the client approved $2M" in out
    assert "3-5 bullet points" in out


def test_list_versions_finds_both_summary_templates():
    versions = list_versions("meeting_summary")
    assert versions == ["meeting_summary_v1", "meeting_summary_v2"]


def test_load_fixture_transcripts_finds_seeded_samples():
    transcripts = load_fixture_transcripts()
    assert "client_kickoff_01" in transcripts
    assert "vendor_pricing_review_02" in transcripts
    assert "Sarah" in transcripts["client_kickoff_01"]


def test_score_summary_flags_preamble():
    metrics = _score_summary("Here is a summary of the call:\n- point one")
    assert metrics["has_preamble"] is True


def test_score_summary_counts_concrete_bullets():
    text = "- Client approved $2.4M budget\n- Team discussed general morale"
    metrics = _score_summary(text)
    assert metrics["bullet_count"] == 2
    assert metrics["concrete_bullet_ratio"] == 0.5


def test_summarize_scores_averages_by_template():
    scores = [
        PromptScore(
            template="v1", transcript_id="a", bullet_count=2, has_preamble=True,
            concrete_bullet_ratio=0.0, word_count=40, input_tokens=100, output_tokens=50, raw_output="",
        ),
        PromptScore(
            template="v1", transcript_id="b", bullet_count=4, has_preamble=False,
            concrete_bullet_ratio=1.0, word_count=20, input_tokens=100, output_tokens=30, raw_output="",
        ),
    ]
    summary = summarize_scores(scores)
    assert summary["v1"]["avg_bullet_count"] == 3
    assert summary["v1"]["preamble_rate"] == 0.5
    assert summary["v1"]["avg_concrete_bullet_ratio"] == 0.5
