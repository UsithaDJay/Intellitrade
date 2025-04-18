class RealTimeDataFeeder:
    def __init__(self, data, retrain_frequency='daily'):
        self.data = data.reset_index(drop=True)
        self.current_index = 0
        self.retrain_frequency = retrain_frequency

    def has_next(self):
        return self.current_index < len(self.data)

    def get_next_day(self):
        next_data = self.data.iloc[[self.current_index]].copy()
        date = next_data['Date'].values[0]
        next_data = next_data.drop(['Date', 'Target'], axis=1)
        self.current_index += 1
        return date, next_data

    def should_retrain(self):
        if self.retrain_frequency == 'daily':
            return True
        elif self.retrain_frequency == 'weekly':
            return self.current_index % 5 == 0
        elif self.retrain_frequency == 'monthly':
            return self.current_index % 21 == 0
        return False