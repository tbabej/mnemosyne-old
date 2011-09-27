#
# schedule.py <Peter.Bienstman@UGent.be>
#

from mnemosyne.libmnemosyne.translator import D_, _
from mnemosyne.libmnemosyne.statistics_page import PlotStatisticsPage


class Schedule(PlotStatisticsPage):

    name = D_("Schedule")
    
    NEXT_WEEK = 1
    NEXT_MONTH = 2
    NEXT_3_MONTHS = 3
    NEXT_6_MONTHS = 4
    NEXT_YEAR = 5
    LAST_WEEK = 6
    LAST_MONTH = 7
    LAST_3_MONTHS = 8
    LAST_6_MONTHS = 9
    LAST_YEAR = 10

    variants = [(NEXT_WEEK, D_("Next week")),
                (NEXT_MONTH, D_("Next month")),
                (NEXT_3_MONTHS, D_("Next 3 months")),
                (NEXT_6_MONTHS, D_("Next 6 months")),
                (NEXT_YEAR, D_("Next year")),
                (LAST_WEEK, D_("Last week")),
                (LAST_MONTH, D_("Last month")),
                (LAST_3_MONTHS, D_("Last 3 months")),
                (LAST_6_MONTHS, D_("Last 6 months")),  
                (LAST_YEAR, D_("Last year"))]

    def retranslate(self):
        self.name = _(self.name)
        for idx, variant in enumerate(self.variants):
            self.variants[idx] = (self.variants[idx][0],
                                  _(self.variants[idx][1]))
   
    def prepare_statistics(self, variant):
        if variant == self.NEXT_WEEK:
            self.x = range(1, 8, 1)
        elif variant == self.NEXT_MONTH:   
            self.x = range(1, 32, 1)
        elif variant == self.NEXT_3_MONTHS:
            self.x = range(1, 92, 1)
        elif variant == self.NEXT_6_MONTHS:
            self.x = range(1, 183, 1)        
        elif variant == self.NEXT_YEAR:
            self.x = range(1, 366, 1)
        elif variant == self.LAST_WEEK:
            self.x = range(-7, 1, 1)
        elif variant == self.LAST_MONTH:
            self.x = range(-31, 1, 1)
        elif variant == self.LAST_3_MONTHS:
            self.x = range(-91, 1, 1)
        elif variant == self.LAST_6_MONTHS:
            self.x = range(-182, 1, 1)
        elif variant == self.LAST_YEAR:
            self.x = range(-365, 1, 1)
        else:
            raise AttributeError, "Invalid variant"
        self.y = [self.scheduler().card_count_scheduled_n_days_from_now(n=day)
                  for day in self.x]
        
            
