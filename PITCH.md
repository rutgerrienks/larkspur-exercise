# PITCH.md

Six lines and a lever. Your words. The last two are scored.

Built: We've fixed the agent loop by removing the errors from the repo and improved some tool descriptions and even connected some new tools (next_available_day and fare_rule) to the LLM so it can use them. Some were made available through an MCP server even.
Does: When the flight is disrupted a customer can give their booking code and name. The agent checks the flight status and cause, it offers replacement flights and quotes the handbook when pushed back.
Number: For five different ticket types the average amount of input tokens is 13k and output tokens is about 1k.
Safety check: Nothing irreversible happens without the customer. There is no auto transferral of (large amounts of) money, hotel approvements or vouchers as these are transferred to humans. 
Next: We'd run through all the possible dialogue options given the data collected from the transcripts to try to cover as much relevant scenario as possible using a nice prioritization mechanism provided by the lever
Still broken: next_available_day does not know how many people are travelling. It is just considering one individual. Also there are no guardrails for the tone of the response yet
Lever: <cost | speed | intelligence>

## Priya asked

Costs:
Wrong:
Runs it:
Left out:
