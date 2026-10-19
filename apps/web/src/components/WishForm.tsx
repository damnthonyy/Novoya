
import { useForm } from "@tanstack/react-form";
import { useState } from "react";
import { useTranslation } from "react-i18next";
type Status = "idle" | "loading" | "error" | "notCovered";


async function submitWish(wish: string) {
    console.log(wish);
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return {
      covered: false,
      message: "Nous ne couvrons pas encore cette destination.",
      suggestions: ["Lisbonne", "Marrakech", "Istanbul"],
    };
  }
  export function WishForm() {
    const [status, setStatus] = useState<Status>("idle");
    const [message, setMessage] = useState("");
    const [suggestions, setSuggestions] = useState<string[]>([]);
    const { t } = useTranslation("wish");
    const { t: tCommon } = useTranslation();
    const { t: tErrors } = useTranslation("errors");
    const form = useForm({
        defaultValues: { wish: "" },
        onSubmit: async ({ value }) => {
          setStatus("loading");
          setSuggestions([]);
          try {
            const result = await submitWish(value.wish);
            if (!result.covered) {
              setMessage(result.message);
              setSuggestions(result.suggestions);
              setStatus("notCovered");
            } else {
              setStatus("idle");
            }
          } catch {
            setStatus("error");
          }
        },
      });

      return (
        <div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              e.stopPropagation();
              form.handleSubmit();
            }}
          >
         <form.Field name="wish">
          {(field) => (
            <textarea
              value={field.state.value}
              onChange={(e) => field.handleChange(e.target.value)}
              placeholder={t("placeholder")}
            />
          )}
        </form.Field>
        <button type="submit" disabled={status === "loading"}>
          {t("send")}
        </button>
      </form>

      {status === "loading" && <p>{tCommon("loading")}</p>}

      {status === "error" && <p>{tErrors("wishFailed")}</p>}

      {status === "notCovered" && (
        <div>
          <p>{message}</p>
          {suggestions.map((destination) => (
            <button
              key={destination}
              type="button"
              
              onClick={() => console.log(destination)}
            >
              {destination}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}