# Sticky Story Shorts – daily run (10:00 Asia/Jerusalem)

Channel: Sticky Story Shorts (UCQxUtr9V_F7Of86totFisLw). Upload via Windsor.ai connector `youtube`, account 126698,
action `upload_video` with video_url = https://raw.githubusercontent.com/yarinedri/stickyStory/main/videos/<file>.mp4
(made_for_kids=false, privacy public, category 24). Never post to Facebook.

Every day, 3 Shorts:
1. **Weekly story episode** (`episodes/story_wN_eK.py`). One story per week (7 episodes). Each episode ends with an A/B choice.
   Before writing episode K, read comments on episode K-1 (Windsor get_data: comment_video_id, comment_text,
   comment_like_count, comment_author). Winner = most-liked comment that clearly picks A or B (tie/no votes: count
   A vs B comments; still nothing: pick the more dramatic option and say "you didn't vote, so I chose"). The episode
   opens by naming the winner ("Most of you said B...").
   Ep 7 resolves the story; next week starts a new one.
2. **Fact** (`episodes/fact_NNN_slug.py`): a real, verifiable fact with a stickman visual, ends with a comment prompt.
   Never repeat a fact (see state/facts.json).
3. **Sticky Town** (`pipeline/town.py`, state in `state/town.json`): population = subscriber_count (Windsor channel data);
   named citizens = authors who commented "I'm in" (any video). Update prev_population, population, named, new_named, day.

Render: `bash setup.sh`, then `cd pipeline && PYTHONPATH=../episodes:. python3 render.py <module> /tmp/ss/out/<name>.mp4`
(town: `python3 town.py /tmp/ss/out/town_dayN.mp4`). Check a few preview frames first.
Copy finished mp4 to `videos/`, commit, push, then upload. Record video ids in state/log.json.
Keep every video distinct (different scenes, script, title) – no templated repeats.
