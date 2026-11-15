# Tuning clips to the game

A clip has its own length, speed and moment of impact; the game has a movement speed, an attack
interval and a corpse time. Fit the clip to the game with numbers, not by eye, then check by eye.
`scripts/measure_clip.gd` prints a clip's length, the root bone's travel and the feet's speed on the
ground.

## Walks and runs: no foot sliding

`measure_clip.gd` finds the frames where the foot is on the ground and takes the median speed of the
foot relative to the root, at the model's game scale. That is the speed the unit must move for the
feet not to slide at playback speed x1:

```
playback speed = movement speed in the game / foot speed measured
```

Examples: a walk whose feet move at 2.3 m/s, on a unit that walks at 3 m/s, plays at x1.3; a run
whose feet move at 4.5 m/s on a unit that flees at 4.5 m/s plays at x1. A clip far from the speed it
is needed at (a run at x0.3) looks like slow motion: pick another clip or change the movement speed
rather than stretching it. Heavy, big creatures have a slower cadence than a human, so a walk played a
little slow suits them, but under about x0.5 it looks wrong.

**Measure the clip you use.** Clips named alike (`run`, `walk`) on the model and in a downloaded file
are different clips; see the name-collision pitfall in `retargeting.md`.

## Attacks: the moment of impact

In many games the damage applies when the attack starts and the animation only decorates it. Then:

- **Skip the wind-up**: start the clip at the swing (`seek(start, true)` after `play()`), so the
  blow visibly lands when the damage does. Find the swing by printing the weapon hand's position every
  0.2 s (it peaks at the top of the raise, then drops fastest to the impact).
- **Fit it into the attack interval**: `(clip length - start) / speed` should be shorter than the
  weapon's interval, or the next swing cuts the last one off.
- A bite or lunge: the head or the shoulders move furthest forward at the impact; the same printing
  works with the head bone.
- A skill's clip that plays from its start (no start offset in the visual): a quick wind-up of about
  0.5 s at the skill's speed is acceptable; pick the speed so the impact lands within a few tenths of
  a second after the sound.

## Loops, root travel and one-shots

- **Imported clips do not loop**; set `loop_mode = LOOP_LINEAR` at run time on the idle, move and
  flee clips of a model that does not use import settings, once per clip (the library is shared by
  every instance: mark the clip with metadata when you have fixed it).
- **Root travel.** A clip that carries the hips forward makes the model snap back every loop. Pin the
  root bone's forward and sideways position to its first key in every key of the looping clip, keep
  the up-and-down bob. (Clips downloaded "In Place" already do not travel; pin them anyway if there
  is sway.)
- **One-shots** (attack, bite, hit, taunt) never loop, so `animation_finished` returns the unit to the
  base clip. A one-shot that must not be cut short (an attack) blocks a flinch; a state that should
  cut it short (running away) clears the one-shot first.
- **A flinch needs a cooldown.** A unit under constant fire would flinch all the time; allow one per
  few seconds of game time (count down in `_process`, which follows `Engine.time_scale`).
- **A big flinch clip fights the movement**: the game keeps moving the unit while it plays, so it
  slides a little. Keep flinches short (play them faster) and rare.

## Death and the end of the night

- Fit the death clip into the corpse time: `speed = clip length / corpse seconds`, and hold the last
  frame.
- **A battle that ends on a unit's death freezes the nodes the units live under** (disabling a parent
  stops its `AnimationPlayer`): a general's death wins the night and the fall stays on its first frame.
  Give a falling visual its own process mode (`PROCESS_MODE_PAUSABLE`, like a cheer) so it plays out
  and still pauses with the menus.

## Checking in play

Log the `AnimationPlayer`'s `current_animation` and `get_playing_speed()` whenever they change during
a real run (a battle with the unit, a sped-up one is fine) and look for every action and the return to
the base clip (`testing-recipes.md`). One screenshot cannot show an animation plays.
