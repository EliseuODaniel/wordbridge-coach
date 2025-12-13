/** Session Counter Component */

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
    <div className="max-w-4xl mx-auto mb-8">
      <div className="bg-gray-800 rounded-xl shadow-sm border border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-100 mb-4 text-center">
          Session Progress
        </h2>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Cards Total */}
          <div className="text-center">
            <div className="text-2xl font-bold text-primary-400">
              {stats.cards_total}
            </div>
            <div className="text-sm text-gray-400">Total Cards</div>
          </div>

          {/* New Cards Today */}
          <div className="text-center">
            <div className="text-2xl font-bold text-warning-400">
              {stats.new_cards_today}
            </div>
            <div className="text-sm text-gray-400">New Today</div>
            <div className="text-xs text-gray-500">
              {newCardsRemaining} remaining
            </div>
          </div>

          {/* Accuracy */}
          <div className="text-center">
            <div className="text-2xl font-bold text-success-400">
              {accuracy}%
            </div>
            <div className="text-sm text-gray-400">Accuracy</div>
            <div className="text-xs text-gray-500">
              {stats.reviews_today} reviews
            </div>
          </div>

          {/* Learning Cards */}
          <div className="text-center">
            <div className="text-2xl font-bold text-info-400">
              {stats.learning_count}
            </div>
            <div className="text-sm text-gray-400">Learning</div>
          </div>
        </div>

        {/* Progress Bar for New Cards */}
        <div className="mt-4">
          <div className="flex justify-between text-sm text-gray-400 mb-1">
            <span>New Card Progress</span>
            <span>{stats.new_cards_today}/{dailyNewLimit}</span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div
              className="bg-warning-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default SessionCounter;
