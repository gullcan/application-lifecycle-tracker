from pytest import CaptureFixture

from application_tracker.demo import main

def test_demo_shows_only_applications_needing_follow_up(
        capsys: CaptureFixture[str],
) -> None:
    main()

    output = capsys.readouterr().out

    assert "All applications: 3" in output
    assert "OpenAI | Backend Engineer | screening" in output

    assert "Anthropic | Python Engineer | interview" not in output
    assert "Github | Platform Engineer | rejected" not in output

    