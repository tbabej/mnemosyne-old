##############################################################################
#
# scheduler.py <Peter.Bienstman@UGent.be>
#
##############################################################################

import logging, random

from mnemosyne.libmnemosyne.start_date import start_date
from mnemosyne.libmnemosyne.card import Card
from mnemosyne.libmnemosyne.scheduler import Scheduler
from mnemosyne.libmnemosyne.plugin_manager import get_database

log = logging.getLogger("mnemosyne")



##############################################################################
#
# SM2Mnemosyne
#
##############################################################################

class SM2Mnemosyne(Scheduler):

    ##########################################################################
    #
    # __init__
    #
    ##########################################################################

    def __init__(self):
        
        Scheduler.__init__(self, name="SM2 Mnemosyne",
                           description="Default scheduler",
                           can_be_unregistered=False)

        self.queue = []


    
    ##########################################################################
    #
    # calculate_initial_interval
    #
    ##########################################################################

    def calculate_initial_interval(self, grade):

        # If this is the first time we grade this card, allow for slightly
        # longer scheduled intervals, as we might know this card from before.

        interval = (0, 0, 1, 3, 4, 5) [grade]
        return interval



    ##########################################################################
    #
    # calculate_interval_noise
    #
    ##########################################################################

    def calculate_interval_noise(self, interval):

        if interval == 0:
            noise = 0
        elif interval == 1:
            noise = random.randint(0,1)
        elif interval <= 10:
            noise = random.randint(-1,1)
        elif interval <= 60:
            noise = random.randint(-3,3)
        else:
            a = .05 * interval
            noise = round(random.uniform(-a,a))

        return noise



    ##########################################################################
    #
    # rebuild_queue
    #
    ##########################################################################
    
    def rebuild_queue(self, learn_ahead = False):

        self.queue = []

        db = get_database()

        if not db.is_loadad():
            return

        update_days_since_start()
    
        # Do the cards that are scheduled for today (or are overdue), but
        # first do those that have the shortest interval, as being a day
        # late on an interval of 2 could be much worse than being a day late
        # on an interval of 50.

        self.queue = [i for i in cards if i.is_due_for_retention_rep()]
        self.queue.sort(key=Card.sort_key_interval)

        if len(self.queue) != 0:
            return

        # Now rememorise the cards that we got wrong during the last stage.
        # Concentrate on only a limited number of grade 0 cards, in order to
        # avoid too long intervals between revisions. If there are too few
        # cards in left in the queue, append more new cards to keep some
        # spread between these last cards.

        limit = config["grade_0_items_at_once"]

        grade_0 = (i for i in cards if i.is_due_for_acquisition_rep() \
                                       and i.lapses > 0 and i.grade == 0)

        grade_0_selected = []

        if limit != 0:
            for i in grade_0:
                for j in grade_0_selected:
                    if cards_are_inverses(i, j):
                        break
                else:
                    grade_0_selected.append(i)

                if len(grade_0_selected) == limit:
                    break

        grade_1 = [i for i in cards if i.is_due_for_acquisition_rep() \
                                       and i.lapses > 0 and i.grade == 1]

        self.queue += 2*grade_0_selected + grade_1

        random.shuffle(self.queue)

        if len(grade_0_selected) == limit or len(self.queue) >= 10: 
            return

        # Now do the cards which have never been committed to long-term
        # memory, but which we have seen before.

        grade_0 = (i for i in cards if i.is_due_for_acquisition_rep() \
                      and i.lapses == 0 and i.acq_reps > 1 and i.grade == 0)

        grade_0_in_queue = len(grade_0_selected)
        grade_0_selected = []

        if limit != 0:
            for i in grade_0:
                for j in grade_0_selected:
                    if cards_are_inverses(i, j):
                        break
                else:
                    grade_0_selected.append(i)

                if len(grade_0_selected) + grade_0_in_queue == limit:
                    break

        grade_1 = [i for i in cards if i.is_due_for_acquisition_rep() \
                      and i.lapses == 0 and i.acq_reps > 1 and i.grade == 1]

        self.queue += 2*grade_0_selected + grade_1

        random.shuffle(self.queue)

        if len(grade_0_selected) + grade_0_in_queue == limit or \
           len(self.queue) >= 10: 
            return

        # Now add some new cards. This is a bit inefficient at the moment as
        # 'unseen' is wastefully created as opposed to being a generator
        # expression. However, in order to use random.choice, there doesn't
        # seem to be another option.

        unseen = [i for i in cards if i.is_due_for_acquisition_rep() \
                                       and i.acq_reps <= 1]

        grade_0_in_queue = sum(1 for i in self.queue if i.grade == 0)/2
        grade_0_selected = []

        if limit != 0 and len(unseen) != 0:    
            while True:
                if get_config("randomise_new_cards") == False:
                    new_card = unseen[0]
                else:
                    new_card = random.choice(unseen)

                unseen.remove(new_card)

                for i in grade_0_selected:
                    if cards_are_inverses(new_card, i):
                        break
                else:
                    grade_0_selected.append(new_card)

                if len(unseen) == 0 or \
                       len(grade_0_selected) + grade_0_in_queue == limit:
                    self.queue += grade_0_selected
                    return      

        # If we get to here, there are no more scheduled cards or new cards
        # to learn. The user can signal that he wants to learn ahead by
        # calling rebuild_revision_queue with 'learn_ahead' set to True.
        # Don't shuffle this queue, as it's more useful to review the
        # earliest scheduled cards first.

        if learn_ahead == False:
            return
        else:
            self.queue = [i for i in cards \
                              if i.qualifies_for_learn_ahead()]

        self.queue.sort(key=Card.sort_key)



    ##########################################################################
    #
    # in_queue
    #
    ##########################################################################

    def in_queue(self, card):
        return card in self.queue



    ##########################################################################
    #
    # remove_from_queue
    #
    #   Remove a single instance of an card from the queue. Necessary when
    #   the queue needs to be rebuilt, and there is still a question pending.
    #
    ##########################################################################

    def remove_from_queue(self, card):

        for i in self.queue:
            if i.id == card.id:
                self.queue.remove(i)
                return


    ##########################################################################
    #
    # get_new_question
    #
    ##########################################################################

    def get_new_question(self, learn_ahead = False):

        # Populate list if it is empty.

        if len(self.queue) == 0:
            rebuild_self.queue(learn_ahead)
            if len(self.queue) == 0:
                return None

        # Pick the first question and remove it from the queue.

        card = self.queue[0]
        self.queue.remove(card)

        return card



    ##########################################################################
    #
    # process_answer
    #
    ##########################################################################

    def process_answer(self, card, new_grade, dry_run=False):

        # When doing a dry run, make a copy to operate on. Note that this
        # leaves the original in cards and the reference in the GUI intact.

        if dry_run:
            card = copy.copy(card)

        # Calculate scheduled and actual interval, taking care of corner
        # case when learning ahead on the same day.

        scheduled_interval = card.next_rep    - card.last_rep
        actual_interval    = days_since_start - card.last_rep

        if actual_interval == 0:
            actual_interval = 1 # Otherwise new interval can become zero.

        if card.is_new():

            # The card is not graded yet, e.g. because it is imported.

            card.acq_reps = 1
            card.acq_reps_since_lapse = 1

            new_interval = calculate_initial_interval(new_grade)

            # Make sure the second copy of a grade 0 card doesn't show
            # up again.

            if not dry_run and card.grade == 0 and new_grade in [2,3,4,5]:
                for i in self.queue:
                    if i.id == card.id:
                        self.queue.remove(i)
                        break

        elif card.grade in [0,1] and new_grade in [0,1]:

            # In the acquisition phase and staying there.

            card.acq_reps += 1
            card.acq_reps_since_lapse += 1

            new_interval = 0

        elif card.grade in [0,1] and new_grade in [2,3,4,5]:

             # In the acquisition phase and moving to the retention phase.

             card.acq_reps += 1
             card.acq_reps_since_lapse += 1

             new_interval = 1

             # Make sure the second copy of a grade 0 card doesn't show
             # up again.

             if not dry_run and card.grade == 0:
                 for i in self.queue:
                     if i.id == card.id:
                         self.queue.remove(i)
                         break

        elif card.grade in [2,3,4,5] and new_grade in [0,1]:

             # In the retention phase and dropping back to the
             # acquisition phase.

             card.ret_reps += 1
             card.lapses += 1
             card.acq_reps_since_lapse = 0
             card.ret_reps_since_lapse = 0

             new_interval = 0

             # Move this card to the front of the list, to have precedence
             # over cards which are still being learned for the first time.

             if not dry_run:
                 cards.remove(card)
                 cards.insert(0,card)

        elif card.grade in [2,3,4,5] and new_grade in [2,3,4,5]:

            # In the retention phase and staying there.

            card.ret_reps += 1
            card.ret_reps_since_lapse += 1

            if actual_interval >= scheduled_interval:
                if new_grade == 2:
                    card.easiness -= 0.16
                if new_grade == 3:
                    card.easiness -= 0.14
                if new_grade == 5:
                    card.easiness += 0.10
                if card.easiness < 1.3:
                    card.easiness = 1.3

            new_interval = 0

            if card.ret_reps_since_lapse == 1:
                new_interval = 6
            else:
                if new_grade == 2 or new_grade == 3:
                    if actual_interval <= scheduled_interval:
                        new_interval = actual_interval * card.easiness
                    else:
                        new_interval = scheduled_interval

                if new_grade == 4:
                    new_interval = actual_interval * card.easiness

                if new_grade == 5:
                    if actual_interval < scheduled_interval:
                        new_interval = scheduled_interval # Avoid spacing.
                    else:
                        new_interval = actual_interval * card.easiness

            # Shouldn't happen, but build in a safeguard.

            if new_interval == 0:
                log.info("Internal error: new interval was zero.")
                new_interval = scheduled_interval

            new_interval = int(new_interval)

        # When doing a dry run, stop here and return the scheduled interval.

        if dry_run:
            return new_interval

        # Add some randomness to interval.

        noise = calculate_interval_noise(new_interval)

        # Update grade and interval.

        card.grade    = new_grade
        card.last_rep = days_since_start
        card.next_rep = days_since_start + new_interval + noise

        # Don't schedule inverse or identical questions on the same day.

        for j in cards:
            if (j.q == card.q and j.a == card.a) or cards_are_inverses(card,j):
                if j != card and j.next_rep == card.next_rep \
                  and card.grade >= 2:
                    card.next_rep += 1
                    noise += 1

        # Create log entry.

        log.info("R %s %d %1.2f | %d %d %d %d %d | %d %d | %d %d | %1.1f",
                    card.id, card.grade, card.easiness,
                    card.acq_reps, card.ret_reps, card.lapses,
                    card.acq_reps_since_lapse, card.ret_reps_since_lapse,
                    scheduled_interval, actual_interval,
                    new_interval, noise, thinking_time)

        return new_interval + noise


    ##########################################################################
    #
    # clear_queue
    #
    ##########################################################################

    def clear_queue(self):

        self.queue = []
