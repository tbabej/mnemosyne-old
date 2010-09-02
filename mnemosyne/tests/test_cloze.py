#
# test_cloze.py <Peter.Bienstman@UGent.be>
#

from mnemosyne_test import MnemosyneTest


class TestCloze(MnemosyneTest):

    def setup(self):
        MnemosyneTest.setup(self)
        from mnemosyne.libmnemosyne.card_types.cloze import ClozePlugin
        for plugin in self.plugins():
            if isinstance(plugin, ClozePlugin):
                plugin.activate()
                break

    def test_validate(self):
        card_type = self.card_type_by_id("5")
        
        fact_data = {"text": "incomplete"}
        assert card_type.is_data_valid(fact_data) == False
        
        fact_data = {"text": "[incomplete"}
        assert card_type.is_data_valid(fact_data) == False
        
        fact_data = {"text": "incomplete]"}
        assert card_type.is_data_valid(fact_data) == False
        
        fact_data = {"text": "[]"}
        assert card_type.is_data_valid(fact_data) == False
        
        fact_data = {"text": "[complete]"}
        assert card_type.is_data_valid(fact_data) == True

    def test_add(self):
        card_type = self.card_type_by_id("5")
        
        fact_data = {"text": "a [b] c"}

        card = self.controller().create_new_cards(fact_data, card_type,
                                          grade=-1, tag_names=["default"])[0]
        self.controller().file_save()

        fact = card.fact
        card = self.database().cards_from_fact(fact)[0]
        
        assert self.database().fact_count() == 1
        assert self.database().card_count() == 1

        card.question()
        card.answer()
                
    def test_edit(self):
        card_type = self.card_type_by_id("5")
        
        fact_data = {"text": "a [b] [c]"}

        card = self.controller().create_new_cards(fact_data, card_type,
                                          grade=-1, tag_names=["default"])[0]
        self.controller().file_save()

        fact = card.fact
        card = self.database().cards_from_fact(fact)[0]
        
        assert self.database().fact_count() == 1
        assert self.database().card_count() == 2

        fact_data = {"text": "a_ [b_] [c_]"}
        self.controller().edit_related_cards(fact, fact_data,
               card_type, new_tag_names=["default2"], correspondence=[])
        
        assert self.database().fact_count() == 1
        assert self.database().card_count() == 2

        fact_data = {"text": "a_ [b_]"}
        self.controller().edit_related_cards(fact, fact_data,
               card_type, new_tag_names=["default2"], correspondence=[])
        
        assert self.database().fact_count() == 1
        assert self.database().card_count() == 1
        
        fact_data = {"text": "a_ [b_] [d] [e]"}
        self.controller().edit_related_cards(fact, fact_data,
               card_type, new_tag_names=["default2"], correspondence=[])
        
        assert self.database().fact_count() == 1
        assert self.database().card_count() == 3
        
