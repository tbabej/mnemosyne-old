#
# test_scheduler.py <Peter.Bienstman@UGent.be>
#

import time
import datetime
import calendar
from mnemosyne_test import MnemosyneTest


class TestScheduler(MnemosyneTest):

    def test_1(self):
        card_type = self.card_type_with_id("1")
        
        fact_data = {"f": "1", "b": "b"}
        card_1 = self.controller().create_new_cards(fact_data, card_type,
                     grade=-1, tag_names=[])[0]
        fact_data = {"f": "2", "b": "b"}        
        card_2 = self.controller().create_new_cards(fact_data, card_type,
                     grade=-1, tag_names=[])[0]
        fact_data = {"f": "3", "b": "b"}
        card_3 = self.controller().create_new_cards(fact_data, card_type,
                     grade=2, tag_names=[])[0]
        fact_data = {"f": "4", "b": "b"}
        card_4 = self.controller().create_new_cards(fact_data, card_type,
                     grade=2, tag_names=[])[0]
        card_4.next_rep -= 1000 * 24 * 60 * 60
        self.database().update_card(card_4)

        assert self.scheduler().next_card() == card_4
        self.scheduler().grade_answer(card_4, 0)
        assert card_4.active == True
        self.database().update_card(card_4)

        card = self.scheduler().next_card()
        self.scheduler().grade_answer(card, 2)
        assert card.active == True
        self.database().update_card(card)
        
        card = self.scheduler().next_card()
        self.scheduler().grade_answer(card, 0)
        self.database().update_card(card)
            
        card = self.scheduler().next_card()
        self.scheduler().grade_answer(card, 1)
        self.database().update_card(card)
        
        card = self.scheduler().next_card()
        self.scheduler().grade_answer(card, 2)
        self.database().update_card(card)
        learned_cards = [card]
        
        card = self.scheduler().next_card()
        assert card not in learned_cards
        self.scheduler().grade_answer(card, 2)
        self.database().update_card(card)
        learned_cards.append(card)
        
        assert self.scheduler().next_card() == None

        # Learn ahead.
        
        assert self.scheduler().next_card(learn_ahead=True) != None

    def test_1_bis(self):
        card_type = self.card_type_with_id("1")
        
        fact_data = {"f": "1", "b": "b"}
        card_1 = self.controller().create_new_cards(fact_data, card_type,
                     grade=-1, tag_names=[])[0]
        fact_data = {"f": "2", "b": "b"}        
        card_2 = self.controller().create_new_cards(fact_data, card_type,
                     grade=-1, tag_names=[])[0]
        fact_data = {"f": "3", "b": "b"}
        card_3 = self.controller().create_new_cards(fact_data, card_type,
                     grade=2, tag_names=[])[0]
        fact_data = {"f": "4", "b": "b"}
        card_4 = self.controller().create_new_cards(fact_data, card_type,
                     grade=2, tag_names=[])[0]
        card_4.next_rep -= 1000 * 24 * 60 * 60
        self.database().update_card(card_4)

        assert self.scheduler().next_card() == card_4
        self.scheduler().grade_answer(card_4, 1)

        assert card_4.active == True
        self.database().update_card(card_4)

        card = self.scheduler().next_card()
        self.scheduler().grade_answer(card, 2)
        assert card.active == True
        self.database().update_card(card)
        
        card = self.scheduler().next_card()
        self.scheduler().grade_answer(card, 0)
        self.database().update_card(card)
            
        card = self.scheduler().next_card()
        self.scheduler().grade_answer(card, 1)
        self.database().update_card(card)
        
        card = self.scheduler().next_card()
        self.scheduler().grade_answer(card, 2)
        self.database().update_card(card)
        learned_cards = [card]
        
        card = self.scheduler().next_card()
        assert card not in learned_cards
        self.scheduler().grade_answer(card, 2)
        self.database().update_card(card)
        learned_cards.append(card)
        
        assert self.scheduler().next_card() == None

        # Learn ahead.
        
        assert self.scheduler().next_card(learn_ahead=True) != None
        
    def test_2(self):
        card_type = self.card_type_with_id("1")
        
        fact_data = {"f": "1", "b": "b"}
        card_1 = self.controller().create_new_cards(fact_data, card_type,
                     grade=-1, tag_names=["default"])[0]
        fact_data = {"f": "2", "b": "b"}        
        card_2 = self.controller().create_new_cards(fact_data, card_type,
                     grade=-1, tag_names=["default"])[0]
        self.config()["non_memorised_cards_in_hand"] = 0
        
        assert self.scheduler().next_card() is None
        
    def test_grade_0_limit(self):
        card_type = self.card_type_with_id("1")
        for i in range(10):
            fact_data = {"f": str(i), "b": "b"}
            self.controller().create_new_cards(fact_data, card_type,
                     grade=-1, tag_names=["default"])[0]    
        self.config()["non_memorised_cards_in_hand"] = 3
        cards = set()
        for i in range(10):
            card = self.scheduler().next_card()
            self.scheduler().grade_answer(card, 0)
            self.database().update_card(card)
            cards.add(card._id)
        assert len(cards) == 3

    def test_learn_ahead(self):
        card_type = self.card_type_with_id("1")
        for i in range(5):
            fact_data = {"f": str(i), "b": "b"}
            self.controller().create_new_cards(fact_data, card_type,
                     grade=5, tag_names=["default"])[0]
        self.review_controller().learning_ahead = True
        for i in range(30):
            card = self.scheduler().next_card(learn_ahead=True)
            self.scheduler().grade_answer(card, 5)
            self.database().update_card(card)
            
    def test_learn_ahead_2(self):
        card_type = self.card_type_with_id("1")
        fact_data = {"f": "1", "b": "b"}
        old_card = self.controller().create_new_cards(fact_data, card_type,
                     grade=5, tag_names=["default"])[0]
        self.review_controller().learning_ahead = True      
        for i in range(3):
            card = self.scheduler().next_card(learn_ahead=True)
            self.scheduler().grade_answer(card, 5)
            self.database().update_card(card)
        fact_data = {"f": "2", "b": "b"}
        new_card = self.controller().create_new_cards(fact_data, card_type,
                     grade=-1, tag_names=["default"])[0]
        assert self.scheduler().next_card() == new_card


    def test_4(self):
        card_type = self.card_type_with_id("1")
        
        fact_data = {"f": "1", "b": "b"}
        card_1 = self.controller().create_new_cards(fact_data, card_type,
                     grade=-1, tag_names=["default"])[0]
        fact_data = {"f": "2", "b": "b"}        
        card_2 = self.controller().create_new_cards(fact_data, card_type,
                     grade=-1, tag_names=["default"])[0]

        card = self.scheduler().next_card()
        self.scheduler().grade_answer(card, 0)
        card = self.scheduler().next_card()
        self.scheduler().grade_answer(card, 0)        
        self.database().update_card(card)

        assert self.scheduler().next_card() != None
        
    def test_5(self):
        card_type = self.card_type_with_id("1")
        
        fact_data = {"f": "1", "b": "b"}
        card_1 = self.controller().create_new_cards(fact_data, card_type,
                     grade=-1, tag_names=["default"])[0]
        fact_data = {"f": "2", "b": "b"}        
        card_2 = self.controller().create_new_cards(fact_data, card_type,
                     grade=-1, tag_names=["default"])[0]

        self.review_controller().show_new_question()
        self.review_controller().grade_answer(0)
        self.review_controller().grade_answer(0)

        assert self.review_controller().card != None
        
    def test_6(self):
        card_1 = None
        self.review_controller().reset()
        for i in range(10):
            fact_data = {"f": "question" + str(i),
                         "b": "answer" + str(i)}
            if i % 2:
                card_type = self.card_type_with_id("1")
            else:
                card_type = self.card_type_with_id("2")            
            card = self.controller().create_new_cards(fact_data, card_type,
                    grade=4, tag_names=["default" + str(i)])[0]
            card.next_rep = time.time() - 24 * 60 * 60
            card.last_rep = card.next_rep - i * 24 * 60 * 60
            self.database().update_card(card)
            if i == 0:
                card_1 = card
        self.review_controller().show_new_question()
        assert self.review_controller().card == card_1
        self.review_controller().grade_answer(0)
        card_1_new = self.database().card(card_1._id, is_id_internal=True)
        assert card_1_new.grade == 0

    def test_learn_ahead_3(self):
        card_type = self.card_type_with_id("1")
        fact_data = {"f": "1", "b": "b"}
        card = self.controller().create_new_cards(fact_data, card_type,
                     grade=-1, tag_names=["default"])[0]
        self.review_controller().show_new_question()
        self.review_controller().grade_answer(5)    
        self.review_controller().learning_ahead = True
        for i in range(10):
            self.review_controller().show_new_question()
            assert self.review_controller().card is not None
            self.review_controller().grade_answer(2)

    def test_learn_ahead_4(self):
        card_type = self.card_type_with_id("1")
        fact_data = {"f": "1", "b": "b"}
        card = self.controller().create_new_cards(fact_data, card_type,
                     grade=5, tag_names=["default"])[0]
        self.review_controller().learning_ahead = True
        self.review_controller().show_new_question()
        self.review_controller().grade_answer(0)
        assert self.review_controller().scheduled_count == 0
                    
    def test_learn_sister_together(self):
        self.config()["memorise_sister_cards_on_same_day"] = True
        card_type = self.card_type_with_id("2")
        fact_data = {"f": "f", "b": "b"}
        card_1, card_2 = self.controller().create_new_cards(fact_data,
          card_type, grade=-1, tag_names=["default"])
        for i in range(7):
            fact_data = {"f": str(i), "b": "b"}
            self.controller().create_new_cards(fact_data, card_type,
                     grade=-1, tag_names=["default"])[0]
        self.review_controller().show_new_question()
        assert self.review_controller().card == card_1
        self.review_controller().grade_answer(5)
        cards = set()
        for i in range(30):
            self.review_controller().grade_answer(1)
            cards.add(self.review_controller().card._id)
        assert card_2._id in cards
        
    def test_learn_sister_together_2(self):
        self.config()["memorise_sister_cards_on_same_day"] = False
        card_type = self.card_type_with_id("2")
        fact_data = {"f": "f", "b": "b"}
        card_1, card_2 = self.controller().create_new_cards(fact_data,
          card_type, grade=-1, tag_names=["default"])
        for i in range(7):
            fact_data = {"f": str(i), "b": "b"}
            self.controller().create_new_cards(fact_data, card_type,
                     grade=-1, tag_names=["default"])[0]
        self.review_controller().show_new_question()
        assert self.review_controller().card == card_1
        self.review_controller().grade_answer(5)
        cards = set()
        for i in range(30):
            self.review_controller().grade_answer(1)
            cards.add(self.review_controller().card._id)
        assert card_2._id not in cards

    def test_learn_sister_together_3(self):
        # Relax requirements if there are not enough cards.
        self.config()["memorise_sister_cards_on_same_day"] = False
        card_type = self.card_type_with_id("2")
        fact_data = {"f": "f", "b": "b"}
        card_1, card_2 = self.controller().create_new_cards(fact_data,
          card_type, grade=-1, tag_names=["default"])
        self.review_controller().show_new_question()
        assert self.review_controller().card == card_1
        self.review_controller().grade_answer(5)
        cards = set()
        for i in range(30):
            self.review_controller().grade_answer(1)
            cards.add(self.review_controller().card._id)
        assert card_2._id in cards

    def test_order(self):
        card_type = self.card_type_with_id("1")
        fact_data = {"f": "1", "b": "b"}
        card_1 = self.controller().create_new_cards(fact_data, card_type,
                     grade=5, tag_names=["default"])[0]
        card_1.next_rep = time.time() - 24 * 60 * 60
        card_1.last_rep = card_1.next_rep - 2 * 24 * 60 * 60
        self.database().update_card(card_1)
        fact_data = {"f": "2", "b": "b"}        
        card_2 = self.controller().create_new_cards(fact_data, card_type,
                     grade=5, tag_names=["default"])[0]
        card_2.next_rep = time.time() - 24 * 60 * 60
        card_2.last_rep = card_2.next_rep - 24 * 60 * 60
        self.database().update_card(card_2)

        # Shortest interval should go first.
        assert self.scheduler().next_card() == card_2

    def test_empty_tag(self):
        card_type = self.card_type_with_id("1")
        fact_data = {"f": "1", "b": "b"}
        card = self.controller().create_new_cards(fact_data, card_type,
                     grade=-1, tag_names=[])[0]     
        self.review_controller().show_new_question()
        assert self.review_controller().card == card
        self.review_controller().grade_answer(2)
        self.review_controller().learning_ahead = True
        self.review_controller().show_new_question()
        assert self.review_controller().card == card

    def test_next_rep_to_interval_string(self):
        sch = self.scheduler()
        now = datetime.datetime(2000, 9, 1, 12, 0)

        next_rep = now + datetime.timedelta(1) 
        sch.next_rep_to_interval_string(\
            sch.midnight_UTC(calendar.timegm(next_rep.timetuple())))
       
        assert sch.next_rep_to_interval_string(\
            sch.midnight_UTC(calendar.timegm(next_rep.timetuple())),
            calendar.timegm(now.timetuple())) == \
            "tomorrow"
        
        next_rep = now + datetime.timedelta(2)        
        assert sch.next_rep_to_interval_string(\
            sch.midnight_UTC(calendar.timegm(next_rep.timetuple())),
            calendar.timegm(now.timetuple())) == \
            "in 2 days"
        
        next_rep = now + datetime.timedelta(32)        
        assert sch.next_rep_to_interval_string(\
            sch.midnight_UTC(calendar.timegm(next_rep.timetuple())),
            calendar.timegm(now.timetuple())) == \
            "in 1 month"
        
        next_rep = now + datetime.timedelta(64)        
        assert sch.next_rep_to_interval_string(\
            sch.midnight_UTC(calendar.timegm(next_rep.timetuple())),
            calendar.timegm(now.timetuple())) == \
            "in 2 months"
        
        next_rep = now + datetime.timedelta(366)        
        assert sch.next_rep_to_interval_string(\
            sch.midnight_UTC(calendar.timegm(next_rep.timetuple())),
            calendar.timegm(now.timetuple())) == \
            "in 1.0 years"
        
        next_rep = now + datetime.timedelta(0)        
        assert sch.next_rep_to_interval_string(\
            sch.midnight_UTC(calendar.timegm(next_rep.timetuple())),
            calendar.timegm(now.timetuple())) == \
            "today"
        
        next_rep = now - datetime.timedelta(1)        
        assert sch.next_rep_to_interval_string(\
            sch.midnight_UTC(calendar.timegm(next_rep.timetuple())),
            calendar.timegm(now.timetuple())) == \
            "yesterday"
        
        next_rep = now - datetime.timedelta(2)        
        assert sch.next_rep_to_interval_string(\
            sch.midnight_UTC(calendar.timegm(next_rep.timetuple())),
            calendar.timegm(now.timetuple())) == \
            "2 days ago"
        
        next_rep = now - datetime.timedelta(32)        
        assert sch.next_rep_to_interval_string(\
            sch.midnight_UTC(calendar.timegm(next_rep.timetuple())),
            calendar.timegm(now.timetuple())) == \
            "1 month ago"
        
        next_rep = now - datetime.timedelta(64)        
        assert sch.next_rep_to_interval_string(\
            sch.midnight_UTC(calendar.timegm(next_rep.timetuple())),
            calendar.timegm(now.timetuple())) == \
            "2 months ago"

        next_rep = now - datetime.timedelta(365)      
        assert sch.next_rep_to_interval_string(\
            sch.midnight_UTC(calendar.timegm(next_rep.timetuple())),
            calendar.timegm(now.timetuple())) == \
            "1.0 years ago"

    def test_last_rep_to_interval_string(self):
        sch = self.scheduler()
        now = datetime.datetime(2000, 9, 1, 12, 0)

        last_rep = now + datetime.timedelta(0)  
        sch.last_rep_to_interval_string(\
            calendar.timegm(last_rep.timetuple()))
        
        last_rep = now + datetime.timedelta(0)        
        assert sch.last_rep_to_interval_string(\
            calendar.timegm(last_rep.timetuple()),
            calendar.timegm(now.timetuple())) == \
            "today"

        last_rep = now - datetime.timedelta(1)        
        assert sch.last_rep_to_interval_string(\
            calendar.timegm(last_rep.timetuple()),
            calendar.timegm(now.timetuple())) == \
            "yesterday"
        
        last_rep = now - datetime.timedelta(2)        
        assert sch.last_rep_to_interval_string(\
            calendar.timegm(last_rep.timetuple()),
            calendar.timegm(now.timetuple())) == \
            "2 days ago"
        
        last_rep = now - datetime.timedelta(32)        
        assert sch.last_rep_to_interval_string(\
            calendar.timegm(last_rep.timetuple()),
            calendar.timegm(now.timetuple())) == \
            "1 month ago"
        
        last_rep = now - datetime.timedelta(64)
        assert sch.last_rep_to_interval_string(\
            calendar.timegm(last_rep.timetuple()),
            calendar.timegm(now.timetuple())) == \
            "2 months ago"

        last_rep = now - datetime.timedelta(365)      
        assert sch.last_rep_to_interval_string(\
            calendar.timegm(last_rep.timetuple()),
            calendar.timegm(now.timetuple())) == \
            "1.0 years ago"

    def test_prefetch(self):
        fact_data = {"f": "question1",
                     "b": "answer1"}
        card_type = self.card_type_with_id("1")
        card_0 = self.controller().create_new_cards(fact_data, card_type,
                                              grade=-1, tag_names=["default"])[0]
        fact_data = {"f": "question2",
                     "b": "answer2"}
        card_1 = self.controller().create_new_cards(fact_data, card_type,
                                              grade=-1, tag_names=["default"])[0]

        self.scheduler()._card_ids_in_queue = [card_0._id, card_1._id, card_1._id]
        assert self.scheduler().is_prefetch_allowed(card_to_grade=card_0) == False
        
    def test_prefetch_2(self):
        fact_data = {"f": "question1",
                     "b": "answer1"}
        card_type = self.card_type_with_id("1")
        card_0 = self.controller().create_new_cards(fact_data, card_type,
                                              grade=-1, tag_names=["default"])[0]
        fact_data = {"f": "question2",
                     "b": "answer2"}
        card_1 = self.controller().create_new_cards(fact_data, card_type,
                                              grade=-1, tag_names=["default"])[0]

        self.scheduler()._card_ids_in_queue = [card_0._id, card_1._id, card_0._id]
        self.review_controller().show_new_question()
        self.review_controller().show_answer()
        self.review_controller().grade_answer(0)
        self.review_controller().show_answer()
        self.review_controller().grade_answer(2)
        self.review_controller().show_answer()
        self.review_controller().grade_answer(0)
        self.review_controller().show_answer()
        self.review_controller().grade_answer(0)
    
    def test_relearn(self):
        fact_data = {"f": "question1",
                     "b": "answer1"}
        card_type = self.card_type_with_id("1")
        card_0 = self.controller().create_new_cards(fact_data, card_type,
                                              grade=5, tag_names=["default"])[0]
        card_0.next_rep = 0
        self.database().update_card(card_0)
        self.review_controller().reset()
        self.review_controller().show_new_question()        
        self.review_controller().show_answer()
        self.review_controller().grade_answer(0)
        self.review_controller().show_answer()
        self.review_controller().grade_answer(0)
        self.review_controller().show_answer()
        self.review_controller().grade_answer(0)
        self.review_controller().show_answer()
        assert self.review_controller().card is not None
        self.review_controller().grade_answer(0)        
        assert self.review_controller().card is not None

    def test_stuck(self):
        fact_data = {"f": "question1",
                     "b": "answer1"}
        card_type = self.card_type_with_id("1")
        card_0 = self.controller().create_new_cards(fact_data, card_type,
              grade=-1, tag_names=["default"])[0]

        self.review_controller().reset()
        self.review_controller().show_new_question()        
        self.review_controller().show_answer()
        self.review_controller().grade_answer(2)

        self.review_controller().learning_ahead = True
        self.review_controller().show_answer()
        self.review_controller().grade_answer(0)
        self.review_controller().learning_ahead = False
        
        fact_data = {"f": "question2",
                     "b": "answer2"}
        card_type = self.card_type_with_id("2")
        card_1, card_2 = self.controller().create_new_cards(fact_data, card_type,
              grade=-1, tag_names=["default"])

        while True:
            self.review_controller().show_answer()
            previous_card_id = self.review_controller().card._id
            if self.review_controller().card._id in [card_1._id, card_2._id]:
                if self.review_controller().card._id == card_1._id:
                    other_card = card_2
                else:
                    other_card = card_1
                self.review_controller().grade_answer(2)
                break
            self.review_controller().grade_answer(0)

        # Now we should get to see the other reverse card and not get stuck on the
        # failed card.

        # We also check whether we keep on alternating between the two
        # remaining cards.
        failed = True
        for i in range(100):
            self.review_controller().show_answer()
            assert self.review_controller().card._id != previous_card_id
            if self.review_controller().card._id == other_card._id:
                failed = False
            previous_card_id = self.review_controller().card._id
            self.review_controller().grade_answer(0)
        assert failed == False

    def test_heartbeat(self):
        self.scheduler().heartbeat()
        self.scheduler()._fact_ids_memorised_expires_at = -1
        self.scheduler().heartbeat()
