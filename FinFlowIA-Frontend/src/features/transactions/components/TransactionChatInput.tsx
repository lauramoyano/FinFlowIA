import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSendChatMessage } from "@/features/transactions/hooks/useSendChatMessage";
import { useCreateTransaction } from "@/features/transactions/hooks/useCreateTransaction";
import { getCategoryLabel } from "@/features/transactions/lib/category-label";
import { TransactionForm } from "@/features/transactions/components/TransactionForm";
import { cn, formatCurrency, formatDate } from "@/shared/lib/utils";
import { Button } from "@/shared/components/ui/Button";
import type {
  FinancialRecommendationResult,
  PeriodSummaryResult,
  ProductionEstimate,
  SalesGoalResult,
  Transaction,
  TransactionType,
} from "@/features/transactions/types/transaction.types";

interface ConfirmedTransactionDraft {
  description: string;
  amount: string;
  transaction_type: TransactionType;
  transaction_date: string;
  category: string;
}

type ChatMessage =
  | { id: string; role: "user"; text: string }
  // The orchestrator needs another piece of data (e.g. amount, or a missing
  // product's cost) before it can continue — `code` is the backend's
  // message code, mapped to a translated string below, interpolated with
  // `params` when present (e.g. {{product}}). Replying continues the same
  // conversation_id.
  | { id: string; role: "assistant"; kind: "question"; code: string; params?: Record<string, string> }
  | { id: string; role: "assistant"; kind: "confirm"; draft: ConfirmedTransactionDraft }
  // Set the instant Confirm is clicked, before the create request resolves —
  // removes the buttons immediately so a fast double-click can't submit the
  // same draft twice (waiting on createMutation.isPending alone leaves a gap
  // between the click and React committing the disabled state).
  | { id: string; role: "assistant"; kind: "confirming"; draft: ConfirmedTransactionDraft }
  | { id: string; role: "assistant"; kind: "estimate_result"; estimate: ProductionEstimate }
  | { id: string; role: "assistant"; kind: "sales_goal_result"; result: SalesGoalResult }
  | {
      id: string;
      role: "assistant";
      kind: "financial_recommendation_result";
      result: FinancialRecommendationResult;
    }
  | { id: string; role: "assistant"; kind: "period_summary_result"; result: PeriodSummaryResult }
  | { id: string; role: "assistant"; kind: "agent_unavailable" }
  | { id: string; role: "assistant"; kind: "error"; errorCode: string }
  | { id: string; role: "assistant"; kind: "saved" };

function errorMessageKey(code: string): string {
  if (code === "no_amount") return "chat.errorNoAmount";
  if (code === "not_a_transaction") return "chat.errorNotATransaction";
  if (code === "follow_up_retry_limit") return "chat.followUpRetryLimit";
  return "chat.errorGeneric";
}

function questionMessageKey(code: string): string {
  if (code === "ask_amount") return "chat.askAmount";
  if (code === "ask_product_quantity") return "chat.askProductQuantity";
  if (code === "ask_unit_cost") return "chat.askUnitCost";
  if (code === "ask_unit_cost_with_history") return "chat.askUnitCostWithHistory";
  if (code === "ask_which_product") return "chat.askWhichProduct";
  if (code === "ask_sale_price") return "chat.askSalePrice";
  if (code === "ask_sale_amount") return "chat.askSaleAmount";
  if (code === "ask_recommendation_costs") return "chat.askRecommendationCosts";
  if (code === "ask_recommendation_costs_linked") return "chat.askRecommendationCostsLinked";
  if (code === "ask_period") return "chat.askPeriod";
  return "chat.errorGeneric";
}

// Money amounts arrive as raw numbers in question params; format them here
// so the translated sentence shows currency.
function formatQuestionParams(params?: Record<string, string>): Record<string, string> | undefined {
  if (!params) return params;
  const out = { ...params };
  for (const key of ["total", "insumos"]) {
    if (out[key] !== undefined) out[key] = formatCurrency(out[key]);
  }
  return out;
}

// Gemini-style "spark" mark: a soft gradient circle instead of a flat brand
// swatch, so the assistant reads as its own distinct presence rather than a
// plain UI element re-using the primary color.
function AssistantAvatar() {
  return (
    <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 via-violet-500 to-fuchsia-500 text-white shadow-sm">
      <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.25}>
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
        />
      </svg>
    </div>
  );
}

function AssistantRow({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3">
      <AssistantAvatar />
      <div className="min-w-0 flex-1 pt-0.5 text-[15px] leading-relaxed">{children}</div>
    </div>
  );
}

// Reserved for assistant turns with real data + actions (confirm a
// transaction, a cost/sales-goal result) — everything else reads as plain
// text, Gemini-style, so the chat doesn't turn into a wall of bubbles.
function AssistantCard({ children, testId }: { children: React.ReactNode; testId?: string }) {
  return (
    <div className="space-y-2 rounded-2xl border bg-muted/40 px-4 py-3 text-sm" data-testid={testId}>
      {children}
    </div>
  );
}

interface PersistedChat {
  text: string;
  messages: ChatMessage[];
  conversationId: string | null;
  nextId: number;
}

// Lives at module level so it outlives the component: switching dashboard
// tabs unmounts the page, and without this the conversation and any
// half-typed text would be lost. Cleared on full page reload.
const persistedChats = new Map<string, PersistedChat>();

interface TransactionChatInputProps {
  // When set, the chat's state is kept under this key across unmounts.
  persistKey?: string;
  onSuccess?: (transaction: Transaction) => void;
  // Lets full-page hosts (e.g. HomePage) give the chat more room than the
  // compact panel it's embedded in on TransactionsPage.
  heightClassName?: string;
}

export function TransactionChatInput({
  persistKey,
  onSuccess,
  heightClassName = "h-[26rem]",
}: TransactionChatInputProps) {
  const { t } = useTranslation("transactions");
  const saved = persistKey ? persistedChats.get(persistKey) : undefined;
  const [text, setText] = useState(saved?.text ?? "");
  const [messages, setMessages] = useState<ChatMessage[]>(saved?.messages ?? []);
  const [editingDraft, setEditingDraft] = useState<ConfirmedTransactionDraft | null>(null);
  // Set while the orchestrator is waiting on a follow-up answer (e.g. the
  // amount); sent back on the next message to continue the same thread.
  // Cleared once a turn resolves (confirm/error/agent_unavailable).
  const [conversationId, setConversationId] = useState<string | null>(
    saved?.conversationId ?? null,
  );
  const sendMessage = useSendChatMessage();
  const createMutation = useCreateTransaction();
  const nextIdRef = useRef(saved?.nextId ?? 0);
  const nextId = () => String(nextIdRef.current++);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  // Synchronous lock, separate from React state: two click events firing
  // back-to-back (faster than React can re-render and disable the button)
  // would otherwise both pass the "is this still a confirm message" check
  // and both call createMutation.mutate(), creating the transaction twice.
  // A ref updates immediately, so the second call sees the lock already set.
  const confirmingIdsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!persistKey) return;
    persistedChats.set(persistKey, {
      text,
      messages,
      conversationId,
      nextId: nextIdRef.current,
    });
  }, [persistKey, text, messages, conversationId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sendMessage.isPending]);

  const pushMessage = (message: ChatMessage) => setMessages((prev) => [...prev, message]);

  const resizeTextarea = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || sendMessage.isPending) return;

    pushMessage({ id: nextId(), role: "user", text: trimmed });
    setText("");
    requestAnimationFrame(resizeTextarea);

    sendMessage.mutate(
      { conversationId, text: trimmed },
      {
        onSuccess: (response) => {
          if (response.kind === "question") {
            setConversationId(response.conversation_id);
            pushMessage({
              id: nextId(),
              role: "assistant",
              kind: "question",
              code: response.message ?? "",
              params: response.message_params ?? undefined,
            });
            return;
          }

          // Every other kind ends this orchestrator thread — the next
          // message (confirm/edit aside) should start a fresh conversation.
          setConversationId(null);

          if (response.kind === "agent_unavailable") {
            pushMessage({ id: nextId(), role: "assistant", kind: "agent_unavailable" });
            return;
          }

          if (response.kind === "estimate_result" && response.estimate) {
            pushMessage({
              id: nextId(),
              role: "assistant",
              kind: "estimate_result",
              estimate: response.estimate,
            });
            return;
          }

          if (response.kind === "sales_goal_result" && response.sales_goal) {
            pushMessage({
              id: nextId(),
              role: "assistant",
              kind: "sales_goal_result",
              result: response.sales_goal,
            });
            return;
          }

          if (response.kind === "financial_recommendation_result" && response.financial_recommendation) {
            pushMessage({
              id: nextId(),
              role: "assistant",
              kind: "financial_recommendation_result",
              result: response.financial_recommendation,
            });
            return;
          }

          if (response.kind === "period_summary_result" && response.period_summary) {
            pushMessage({
              id: nextId(),
              role: "assistant",
              kind: "period_summary_result",
              result: response.period_summary,
            });
            return;
          }

          const draft = response.draft;
          if (response.kind === "confirm_transaction" && draft?.amount && draft.transaction_type) {
            pushMessage({
              id: nextId(),
              role: "assistant",
              kind: "confirm",
              draft: {
                description: draft.description,
                amount: draft.amount,
                transaction_type: draft.transaction_type,
                transaction_date: draft.transaction_date,
                category: draft.category,
              },
            });
            return;
          }

          pushMessage({
            id: nextId(),
            role: "assistant",
            kind: "error",
            errorCode: response.error_code ?? draft?.error ?? "errorGeneric",
          });
        },
        onError: () => {
          setConversationId(null);
          pushMessage({ id: nextId(), role: "assistant", kind: "error", errorCode: "errorGeneric" });
        },
      },
    );
  };

  const handleConfirm = (messageId: string, draft: ConfirmedTransactionDraft) => {
    if (confirmingIdsRef.current.has(messageId)) return;
    confirmingIdsRef.current.add(messageId);

    // Optimistically lock this message's buttons before the request resolves.
    setMessages((prev) =>
      prev.map((m) =>
        m.role === "assistant" && m.kind === "confirm" && m.id === messageId
          ? { ...m, kind: "confirming" as const }
          : m,
      ),
    );

    createMutation.mutate(draft, {
      onSuccess: (transaction) => {
        // Drop the summary card now that it's done its job — otherwise it's
        // stuck showing a spinner forever even though the save succeeded,
        // since nothing else ever transitions its kind away from "confirming".
        setMessages((prev) => prev.filter((m) => m.id !== messageId));
        pushMessage({ id: nextId(), role: "assistant", kind: "saved" });
        onSuccess?.(transaction);
      },
      onError: () => {
        // Let the user retry if the create call itself failed.
        confirmingIdsRef.current.delete(messageId);
        setMessages((prev) =>
          prev.map((m) =>
            m.role === "assistant" && m.kind === "confirming" && m.id === messageId
              ? { ...m, kind: "confirm" as const }
              : m,
          ),
        );
      },
    });
  };

  if (editingDraft) {
    return (
      <TransactionForm
        defaultValues={editingDraft}
        onSuccess={(transaction) => {
          setEditingDraft(null);
          pushMessage({ id: nextId(), role: "assistant", kind: "saved" });
          onSuccess?.(transaction);
        }}
        onCancel={() => setEditingDraft(null)}
      />
    );
  }

  return (
    <div className={cn("flex flex-col", heightClassName)}>
      <div
        className="flex-1 space-y-5 overflow-y-auto px-1 py-2 sm:px-2"
        data-testid="chat-messages"
      >
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-sky-400 via-violet-500 to-fuchsia-500 text-white shadow-sm">
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
                />
              </svg>
            </div>
            <p className="max-w-sm text-sm text-muted-foreground">{t("chat.emptyHint")}</p>
          </div>
        )}

        {messages.map((msg) => {
          if (msg.role === "user") {
            return (
              <div key={msg.id} className="flex justify-end">
                <div className="max-w-[80%] rounded-3xl bg-muted px-4 py-2.5 text-[15px] text-foreground">
                  {msg.text}
                </div>
              </div>
            );
          }

          if (msg.kind === "confirm" || msg.kind === "confirming") {
            const { draft } = msg;
            return (
              <AssistantRow key={msg.id}>
                <AssistantCard>
                  <p>
                    {t("chat.confirmSummary", {
                      type: t(draft.transaction_type === "income" ? "list.income" : "list.expense"),
                      amount: formatCurrency(draft.amount),
                      category: getCategoryLabel(t, draft.category),
                      date: formatDate(draft.transaction_date),
                    })}
                  </p>
                  <div className="flex gap-2 pt-1">
                    <Button
                      size="sm"
                      onClick={() => handleConfirm(msg.id, draft)}
                      isLoading={msg.kind === "confirming"}
                      disabled={msg.kind === "confirming"}
                      data-testid="chat-confirm"
                    >
                      {t("chat.confirmButton")}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditingDraft(draft)}
                      disabled={msg.kind === "confirming"}
                      data-testid="chat-edit"
                    >
                      {t("chat.editButton")}
                    </Button>
                  </div>
                </AssistantCard>
              </AssistantRow>
            );
          }

          if (msg.kind === "question") {
            return (
              <AssistantRow key={msg.id}>
                <p data-testid="chat-question">{t(questionMessageKey(msg.code), formatQuestionParams(msg.params))}</p>
              </AssistantRow>
            );
          }

          if (msg.kind === "estimate_result") {
            const { estimate } = msg;
            return (
              <AssistantRow key={msg.id}>
                <AssistantCard testId="chat-estimate-result">
                  <ul className="space-y-1">
                    {estimate.items.map((item, index) => (
                      <li key={index}>
                        {t("chat.estimateLine", {
                          quantity: item.quantity,
                          product: item.product_name,
                          subtotal: formatCurrency(item.subtotal),
                        })}
                      </li>
                    ))}
                  </ul>
                  <p className="font-semibold">
                    {t("chat.estimateTotal", { total: formatCurrency(estimate.total_estimated_cost) })}
                  </p>
                  {estimate.projected_revenue && estimate.estimated_profit && (
                    <p>
                      {t("chat.estimateProfitLine", {
                        revenue: formatCurrency(estimate.projected_revenue),
                        profit: formatCurrency(estimate.estimated_profit),
                      })}
                    </p>
                  )}
                </AssistantCard>
              </AssistantRow>
            );
          }

          if (msg.kind === "sales_goal_result") {
            const { result } = msg;
            return (
              <AssistantRow key={msg.id}>
                <AssistantCard testId="chat-sales-goal-result">
                  {result.items.length > 1 && <p>{t("chat.salesGoalSplitIntro")}</p>}
                  <ul className="space-y-1">
                    {result.items.map((item, index) => (
                      <li key={index}>
                        {result.items.length > 1
                          ? t("chat.salesGoalItemLine", {
                              quantity: item.quantity_needed,
                              product: item.product_name,
                              price: formatCurrency(item.unit_sale_price),
                              investment: formatCurrency(item.insumos_investment),
                            })
                          : t("chat.salesGoalQuantityLine", {
                              quantity: item.quantity_needed,
                              product: item.product_name,
                              price: formatCurrency(item.unit_sale_price),
                            })}
                      </li>
                    ))}
                  </ul>
                  <p>
                    {t("chat.salesGoalInvestmentLine", {
                      investment: formatCurrency(result.insumos_investment),
                    })}
                  </p>
                  <p className="font-semibold">
                    {t("chat.salesGoalProfitLine", { profit: formatCurrency(result.estimated_profit) })}
                  </p>
                </AssistantCard>
              </AssistantRow>
            );
          }

          if (msg.kind === "financial_recommendation_result") {
            const { result } = msg;
            const hasDebt = parseFloat(result.pending_debt_total) > 0;
            return (
              <AssistantRow key={msg.id}>
                <AssistantCard testId="chat-financial-recommendation-result">
                  <ul className="space-y-1">
                    {result.items.map((item, index) => (
                      <li key={index}>
                        {t("chat.recommendationLine", {
                          label: item.label,
                          amount: formatCurrency(item.amount),
                          percentage: item.percentage,
                        })}
                      </li>
                    ))}
                  </ul>
                  <p className="font-semibold">
                    {t("chat.recommendationNet", { net: formatCurrency(result.net_amount) })}
                  </p>
                  {result.insumos_linked_products && result.insumos_linked_products.length > 0 && (
                    <p className="text-muted-foreground">
                      {t("chat.recommendationInsumosLinked", {
                        products: result.insumos_linked_products.join(", "),
                      })}
                    </p>
                  )}
                  {hasDebt && (
                    <p className="text-amber-700 dark:text-amber-400">
                      {t("chat.recommendationDebtWarning", {
                        debt: formatCurrency(result.pending_debt_total),
                      })}
                    </p>
                  )}
                </AssistantCard>
              </AssistantRow>
            );
          }

          if (msg.kind === "period_summary_result") {
            const { current, previous } = msg.result;
            return (
              <AssistantRow key={msg.id}>
                <AssistantCard testId="chat-period-summary-result">
                  <p className="font-semibold">{current.label}</p>
                  <p>{t("chat.periodIncomeLine", { income: formatCurrency(current.total_income) })}</p>
                  <p>{t("chat.periodExpensesLine", { expenses: formatCurrency(current.total_expenses) })}</p>
                  <p className="font-semibold">
                    {t("chat.periodBalanceLine", { balance: formatCurrency(current.balance) })}
                  </p>
                  {previous && (
                    <>
                      <p className="pt-2 font-semibold">{previous.label}</p>
                      <p>{t("chat.periodIncomeLine", { income: formatCurrency(previous.total_income) })}</p>
                      <p>
                        {t("chat.periodExpensesLine", { expenses: formatCurrency(previous.total_expenses) })}
                      </p>
                      <p className="font-semibold">
                        {t("chat.periodBalanceLine", { balance: formatCurrency(previous.balance) })}
                      </p>
                    </>
                  )}
                </AssistantCard>
              </AssistantRow>
            );
          }

          if (msg.kind === "agent_unavailable") {
            return (
              <AssistantRow key={msg.id}>
                <p data-testid="chat-agent-unavailable">{t("chat.agentUnavailable")}</p>
              </AssistantRow>
            );
          }

          if (msg.kind === "error") {
            return (
              <AssistantRow key={msg.id}>
                <p className="text-destructive" data-testid="chat-error">
                  {t(errorMessageKey(msg.errorCode))}
                </p>
              </AssistantRow>
            );
          }

          return (
            <AssistantRow key={msg.id}>
              <p className="text-green-700 dark:text-green-400">{t("chat.savedMessage")}</p>
            </AssistantRow>
          );
        })}

        {sendMessage.isPending && (
          <AssistantRow>
            <div className="inline-flex items-center gap-1 py-1">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.3s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:-0.15s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground" />
            </div>
          </AssistantRow>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="mx-auto mt-3 w-full max-w-3xl">
        <div
          className={cn(
            "flex items-end gap-2 rounded-[1.75rem] border bg-background px-3 py-2 shadow-sm",
            "focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 focus-within:ring-offset-background",
          )}
        >
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => {
              setText(e.target.value);
              resizeTextarea();
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={t("chat.placeholder")}
            rows={1}
            className="max-h-40 flex-1 resize-none bg-transparent px-2 py-2 text-[15px] leading-relaxed outline-none placeholder:text-muted-foreground"
            data-testid="chat-text-input"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={!text.trim() || sendMessage.isPending}
            aria-label={t("chat.send")}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-colors hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-40"
            data-testid="chat-send"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 19V5m0 0l-6 6m6-6l6 6" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
