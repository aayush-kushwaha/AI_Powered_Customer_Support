_memory = {}


def get_history(session_id: str):
    return _memory.get(session_id, []).copy()


def append_turn(session_id: str, role: str, text: str) -> None:
    """
    Add a new turn (message) to the session history.
    
    Args:
        session_id: The ID of the session.
        role: The role of the speaker (e.g., 'user' or 'assistant').
        text: The content of the message.
    """
    # If the session doesn't exist yet, create a new empty list for it
    if session_id not in _memory:
        _memory[session_id] = []
        
    # Append the new message as a dictionary
    _memory[session_id].append({
        "role": role, 
        "text": text
    })


def trim_history(session_id: str, max_turns: int = 6) -> None:
    """
    Limit the chat history to the most recent turns.
    
    Args:
        session_id: The ID of the session to trim.
        max_turns: The maximum number of turns to keep (default is 6).
    """
    # Get the current history; default to empty list if not found
    turns = _memory.get(session_id, [])
    
    # If the history is longer than the limit, keep only the last 'max_turns'
    if len(turns) > max_turns:
        # Slice the list to keep the last N items
        _memory[session_id] = turns[-max_turns:]
