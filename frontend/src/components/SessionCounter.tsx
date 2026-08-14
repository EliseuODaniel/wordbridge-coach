/** Session Counter Component */

import InfoTooltip from './InfoTooltip';

interface StatsData {
  cards_total: number;
  new_count: number;
  learning_count: number;
  review_count: number;
  mature_count: number;
  reviews_today: number;
  accuracy_today: number;
  new_cards_today: number;
  upcoming_reviews: Record<string, number>;
}

interface SessionCounterProps {
  stats: StatsData;
  dailyNewLimit?: number;
}

const SessionCounter: React.FC<SessionCounterProps> = ({ stats, dailyNewLimit = 15 }) => {
  const accuracy = Math.round(stats.accuracy_today * 100);
  const newCardsRemaining = Math.max(0, dailyNewLimit - stats.new_cards_today);
  const progressPercent = Math.min(100, (stats.new_cards_today / dailyNewLimit) * 100);

  return (
    <section className="surface-card mb-5 px-3 py-3 sm:px-4" data-testid="session-counter" aria-label="Resumo da sessão">
      <div className="grid grid-cols-2 items-center gap-3 sm:grid-cols-5 sm:divide-x sm:divide-white/[0.07]">
        <div className="px-2">
          <div className="text-lg font-semibold tabular-nums text-primary-300">{stats.cards_total}</div>
          <div className="text-[11px] text-gray-500">cards disponíveis</div>
        </div>
        <div className="px-2">
          <div className="text-lg font-semibold tabular-nums text-amber-300">{stats.new_cards_today}</div>
          <div className="text-[11px] text-gray-500">novos hoje · {newCardsRemaining} restantes</div>
        </div>
        <div className="px-2">
          <div className="text-lg font-semibold tabular-nums text-emerald-300">{accuracy}%</div>
          <div className="text-[11px] text-gray-500">precisão · {stats.reviews_today} revisões</div>
        </div>
        <div className="px-2">
          <div className="text-lg font-semibold tabular-nums text-cyan-300">{stats.learning_count}</div>
          <div className="text-[11px] text-gray-500">em aprendizagem</div>
        </div>
        <div className="col-span-2 flex items-center gap-3 px-2 sm:col-span-1">
          <div className="min-w-0 flex-1">
            <div className="mb-1 flex justify-between text-[10px] text-gray-500"><span>Meta diária</span><span>{stats.new_cards_today}/{dailyNewLimit}</span></div>
            <div className="h-1.5 overflow-hidden rounded-full bg-white/[0.07]">
              <div className="h-full rounded-full bg-gradient-to-r from-primary-400 to-teal-300 transition-all duration-300" style={{ width: `${progressPercent}%` }} />
            </div>
          </div>
          <InfoTooltip label="Sobre as métricas da sessão">
            Os números combinam seu progresso acumulado com a atividade de hoje. A meta diária limita palavras novas sem impedir revisões vencidas.
          </InfoTooltip>
        </div>
      </div>
    </section>
  );
};

export default SessionCounter;
