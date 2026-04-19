import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Wand2, Loader2 } from "lucide-react";
import { toast } from "sonner";

/**
 * ============================================================
 *  RewriteInstructions Page
 * ------------------------------------------------------------
 *  COMPONENT STRUCTURE:
 *   - Header (title + subtitle)
 *   - Input Card:
 *       • <Textarea> for messy instructions
 *       • Small "wand" icon button (widget) inside the input area
 *       • Main "Rewrite" button below
 *   - Output Card:
 *       • Displays the formatted response from the backend
 *       • Preserves line breaks via `whitespace-pre-wrap`
 *
 *  STATE:
 *   - inputText : string  → user's raw text
 *   - output    : string  → formatted result from API
 *   - loading   : boolean → controls spinner + disables button
 *
 *  API:
 *   - POST {API_URL}/rewrite
 *   - Body:     { text: string }
 *   - Response: { result: string }
 * ============================================================
 */

// 🔌 PLUG YOUR BACKEND URL HERE
// Example: "https://api.yourdomain.com"  — leave empty "" for same-origin "/rewrite"
const API_BASE_URL = "";

const Index = () => {
  // ---- State ----
  const [inputText, setInputText] = useState("");
  const [output, setOutput] = useState("");
  const [loading, setLoading] = useState(false);

  /**
   * handleRewrite
   * -------------
   * Sends the user's text to the backend and stores the formatted result.
   * Triggered by both the main "Rewrite" button and the small widget icon.
   */
  const handleRewrite = async () => {
    // Guard: don't call API on empty input
    if (!inputText.trim()) {
      toast.error("Please enter some text to rewrite.");
      return;
    }

    setLoading(true);
    setOutput("");

    try {
      // ---- API CALL ----
      const response = await fetch(`${API_BASE_URL}/rewrite`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: inputText }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data: { result: string } = await response.json();
      setOutput(data.result ?? "");
    } catch (err) {
      console.error("Rewrite API error:", err);
      toast.error("Failed to rewrite. Check the backend connection.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-background px-4 py-12">
      <div className="mx-auto max-w-3xl space-y-8">
        {/* ---- Header ---- */}
        <header className="space-y-2 text-center">
          <h1 className="text-4xl font-bold tracking-tight text-foreground">
            Rewrite Instructions
          </h1>
          <p className="text-muted-foreground">
            Paste messy instructions and get a clean, formatted version.
          </p>
        </header>

        {/* ---- Input Card ---- */}
        <Card className="p-5">
          <div className="relative">
            <Textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Paste your messy instructions here..."
              className="min-h-[200px] resize-y pr-12 text-base"
              disabled={loading}
            />

            {/* Small widget-style icon button (same action as main button) */}
            <Button
              type="button"
              size="icon"
              variant="ghost"
              onClick={handleRewrite}
              disabled={loading || !inputText.trim()}
              aria-label="Rewrite"
              title="Rewrite"
              className="absolute right-2 top-2 h-8 w-8 text-muted-foreground hover:text-foreground"
            >
              <Wand2 className="h-4 w-4" />
            </Button>
          </div>

          {/* Main Rewrite button */}
          <div className="mt-4 flex justify-end">
            <Button
              onClick={handleRewrite}
              disabled={loading || !inputText.trim()}
              className="min-w-[140px]"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Rewriting...
                </>
              ) : (
                <>
                  <Wand2 className="mr-2 h-4 w-4" />
                  Rewrite
                </>
              )}
            </Button>
          </div>
        </Card>

        {/* ---- Output Card ---- */}
        {(output || loading) && (
          <Card className="p-5">
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Formatted Output
            </h2>

            {loading ? (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Generating clean instructions...</span>
              </div>
            ) : (
              // `whitespace-pre-wrap` preserves line breaks from the API response
              <p className="whitespace-pre-wrap text-base leading-relaxed text-foreground">
                {output}
              </p>
            )}
          </Card>
        )}
      </div>
    </main>
  );
};

export default Index;
