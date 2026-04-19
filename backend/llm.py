"""
llm_client.py
─────────────────────────────────────────────────────────────────────────────
Production-style LangChain module for rewriting raw instruction text into
clean, numbered, step-wise instructions using the "ngroq" LLM provider.

HOW TO INTEGRATE (e.g., in a FastAPI route):
    from llm_client import rewrite_instructions

    @app.post("/rewrite")
    def rewrite(payload: dict):
        result = rewrite_instructions(payload["text"])
        return {"output": result}

TO SWAP THE LLM PROVIDER:
    1. Replace the `ChatGroq` import with your new provider's LangChain chat class.
    2. Update MODEL_NAME and API_KEY_ENV_VAR to match the new provider.
    3. The rest of the code (prompt, chain, function) stays the same.
─────────────────────────────────────────────────────────────────────────────
"""

import os
from langchain_groq import ChatGroq                      # ← swap this import to change provider
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — CONFIGURATION
# All provider-specific settings live here so swapping is a one-line change.
# ─────────────────────────────────────────────────────────────────────────────


# Pull the API key from the environment.
# Replace this block if your provider uses a different auth mechanism.
NGROQ_API_KEY = os.environ.get("AGROQ_API_KEY")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — LLM INITIALIZATION
# Instantiate the LangChain-compatible chat model.
# To swap provider: replace `ChatGroq(...)` with e.g. `ChatOpenAI(...)`.
# ─────────────────────────────────────────────────────────────────────────────

llm = ChatGroq(
    api_key=NGROQ_API_KEY,
    model=MODEL_NAME,
    temperature=0,          # 0 = deterministic / consistent formatting output
    max_tokens=2048,        # raise if instructions are very long
)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    max_tokens=2000,
)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — SYSTEM PROMPT
# This is the core formatting brain. Edit SYSTEM_PROMPT to change behaviour.
# Rules encoded here:
#   • Convert freeform paragraph → numbered list
#   • 1 instruction = 1 atomic operation
#   • Never split a single logical operation across steps
#   • Append tab suffix: CPT → "in procs tab" | ICD → "in diags tab"
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a precise medical-billing instruction formatter.

RULES (follow strictly, no exceptions):
1. Convert the user's paragraph into a numbered list of step-by-step instructions.
2. Each numbered step must represent exactly ONE atomic operation — do not combine
   unrelated operations, and do not split a single logical operation across steps.
3. At the end of every instruction, append the correct tab suffix:
   - If the instruction involves CPT codes → append "in procs tab"
   - If the instruction involves ICD codes → append "in diags tab"
4. Standardise date formats to MM/DD/YYYY.
5. Use "default date" verbatim when no explicit date is given for a field.
6. Do not add explanations, headers, or extra commentary — output ONLY the
   numbered list.

────────────────────────────────────────────
FEW-SHOT EXAMPLE
────────────────────────────────────────────
INPUT:
Please update custom version for payers HSPC1, HSPIL, HSPTN. Change the DOS TO \
to 12/31/2013 for CPT codes 0521F, 1125F, 1126F, 1158F, 1170F. Add codes 0521F, \
1125F, 1126F, 1158F, 1170F and 1111F with another line entry as a deny condition \
DOS FROM 1/1/2014 and DOS TO with default date. Set override flag and change the \
DOS to 12/31/2013 for code 1111F. Add code 1160F as a deny condition with DOS FROM \
default date and DOS TO 12/31/2013 with override. Add code 1160F with another line \
entry DOS FROM 1/1/2014 and DOS TO with default date as a deny condition.

OUTPUT:
1. Update custom version for payers HSPC1, HSPIL, HSPTN and set DOS TO to 12/31/2013 for CPT codes 0521F, 1125F, 1126F, 1158F, 1170F in procs tab.
2. Add CPT codes 0521F, 1125F, 1126F, 1158F, 1170F and 1111F as deny condition entries with DOS FROM 01/01/2014 and DOS TO as default date in procs tab.
3. Update CPT code 1111F by setting override flag and changing DOS TO to 12/31/2013 in procs tab.
4. Add CPT code 1160F as a deny condition entry with DOS FROM as default date, DOS TO as 12/31/2013, and override enabled in procs tab.
5. Add CPT code 1160F as a deny condition entry with DOS FROM 01/01/2014 and DOS TO as default date in procs tab.
────────────────────────────────────────────

Now format the following input using the same rules and style.
"""


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — PROMPT TEMPLATE
# LangChain ChatPromptTemplate wires the system prompt + user message together.
# The {user_input} placeholder is filled at call time by `rewrite_instructions`.
# ─────────────────────────────────────────────────────────────────────────────

prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),          # formatting rules + few-shot example
    ("human", "{user_input}"),          # raw instruction text from the caller
])


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — CHAIN ASSEMBLY
# LangChain Expression Language (LCEL) pipe: prompt → llm → string parser.
# StrOutputParser extracts the plain text from the LLM's response object.
# ─────────────────────────────────────────────────────────────────────────────

chain = prompt_template | llm | StrOutputParser()


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — PUBLIC FUNCTION
# This is the only symbol you need to import from this module.
#
# Usage:
#   from llm_client import rewrite_instructions
#   formatted = rewrite_instructions("Update payer HSPC1 for CPT 99213...")
# ─────────────────────────────────────────────────────────────────────────────

def rewrite_instructions(text: str) -> str:
    """
    Accepts raw instruction text and returns formatted, numbered step-wise
    instructions with correct tab suffixes (procs tab / diags tab).

    Args:
        text: Free-form instruction paragraph from the user.

    Returns:
        A numbered list of clean, atomic instructions as a single string.

    Raises:
        ValueError: If the input text is empty or whitespace-only.
        Exception:  Propagates any LLM/network error to the caller so the
                    API layer can handle it (log, return 500, retry, etc.).
    """
    if not text or not text.strip():
        raise ValueError("Input text must not be empty.")

    # Invoke the chain — this is the only line that makes a network call.
    result: str = chain.invoke({"user_input": text.strip()})

    return result.strip()


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — QUICK SMOKE TEST
# Run `python llm_client.py` directly to verify the integration end-to-end.
# Remove or guard this block before deploying to production.
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sample_input = (
        "Please update custom version for payers HSPC1, HSPIL, HSPTN. "
        "Change the DOS TO to 12/31/2013 for CPT codes 0521F, 1125F, 1126F, "
        "1158F, 1170F. Add codes 0521F, 1125F, 1126F, 1158F, 1170F and 1111F "
        "with another line entry as a deny condition DOS FROM 1/1/2014 and DOS TO "
        "with default date. Set override flag and change the DOS to 12/31/2013 "
        "for code 1111F. Add code 1160F as a deny condition with DOS FROM default "
        "date and DOS TO 12/31/2013 with override. Add code 1160F with another "
        "line entry DOS FROM 1/1/2014 and DOS TO with default date as a deny condition."
    )

    # print("─── INPUT ───")
    # print(sample_input)
    # print("\n─── OUTPUT ───")
    # print(rewrite_instructions(sample_input))