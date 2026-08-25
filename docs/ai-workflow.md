# AI Workflow

## Initial understanding

Input:
- user's free-text symptom description

Output:
- symptoms
- duration
- severity
- context
- missing information

## Adaptive question selection

After each valid answer, Gemini receives:
- original symptom description
- current known information
- previous answers
- questions already asked

It returns either:
- `should_continue = true` + exactly one useful question, or
- `should_continue = false` when enough information exists for cautious guidance.

The backend also rejects duplicate questions and enforces a maximum turn count.

## Answer interpretation

Gemini classifies the answer as:
- answer
- clarification
- unrelated

It also extracts newly mentioned symptoms and explicit facts.

## Final guidance

The final output is structured into:
- summary
- urgency
- recommended action
- why
- warning signs
- care level
- disclaimer

The output is intentionally non-diagnostic.
