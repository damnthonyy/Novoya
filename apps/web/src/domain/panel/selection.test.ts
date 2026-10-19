import { describe, expect, it } from 'vitest'

import { answerPanelErrorKey, initialSelection, selectedTags, toggleTag } from './selection'

const mood = {
  id: 'mood',
  multi: true,
  tags: [
    { id: 'calm', preselected: true },
    { id: 'sea', preselected: true },
    { id: 'culture', preselected: false },
  ],
}
const pace = {
  id: 'pace',
  multi: false,
  tags: [
    { id: 'slow', preselected: true },
    { id: 'busy', preselected: true },
  ],
}

describe('initialSelection', () => {
  it('picks the preselected tags, one at most in a single-choice section', () => {
    expect(initialSelection([mood, pace])).toEqual({ mood: ['calm', 'sea'], pace: ['slow'] })
  })
})

describe('toggleTag', () => {
  it('adds and removes a tag in a multiple-choice section', () => {
    const added = toggleTag({ mood: ['calm'] }, mood, 'culture')
    expect(added.mood).toEqual(['calm', 'culture'])
    expect(toggleTag(added, mood, 'calm').mood).toEqual(['culture'])
  })

  it('replaces the tag in a single-choice section, and can clear it', () => {
    const replaced = toggleTag({ pace: ['slow'] }, pace, 'busy')
    expect(replaced.pace).toEqual(['busy'])
    expect(toggleTag(replaced, pace, 'busy').pace).toEqual([])
  })

  it('does not change the selection it was given', () => {
    const before = { mood: ['calm'] }
    toggleTag(before, mood, 'sea')
    expect(before).toEqual({ mood: ['calm'] })
  })
})

describe('selectedTags', () => {
  it('lists every picked tag with its section', () => {
    expect(selectedTags({ mood: ['calm', 'sea'], pace: [] })).toEqual([
      { section: 'mood', tag: 'calm' },
      { section: 'mood', tag: 'sea' },
    ])
  })
})

describe('answerPanelErrorKey', () => {
  it('explains the API errors, with a fallback', () => {
    expect(answerPanelErrorKey('invalid_answers')).toBe('answers.invalid')
    expect(answerPanelErrorKey('wish_not_found')).toBe('answers.wishNotFound')
    expect(answerPanelErrorKey('invalid_transition')).toBe('answers.alreadyAnswered')
    expect(answerPanelErrorKey(undefined)).toBe('answers.unknown')
  })
})
