from app.services.rag import generate_conversation_summary

previous_summary = """
The user is learning machine learning.
They have studied supervised learning.
"""

new_turns = """
User: What is a random forest?

Assistant: A random forest is an ensemble learning
algorithm that combines multiple decision trees
to improve prediction accuracy and reduce overfitting.
"""

result = generate_conversation_summary(
    previous_summary=previous_summary,
    new_turns=new_turns
)

print("\nUPDATED SUMMARY:\n")
print(result)