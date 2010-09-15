#
# test_render_chain.py <Peter.Bienstman@UGent.be>
#

from mnemosyne_test import MnemosyneTest
from mnemosyne.libmnemosyne.filter import Filter
from mnemosyne.libmnemosyne.renderer import Renderer


class TestRenderChain(MnemosyneTest):
    
    def test_add_filter(self):      
        fact_data = {"q": "question",
                     "a": "answer"}
        card_type_1 = self.card_type_by_id("1")
        card = self.controller().create_new_cards(fact_data, card_type_1,
            grade=-1, tag_names=["default"])[0]

        class MyFilter(Filter):
            def run(self, text):
                return "666"

        self.render_chain().register_filter(MyFilter)
        assert "666" in card.question()
    
        assert type(self.render_chain()._filters[0]) \
               != type(MyFilter(self.mnemosyne.component_manager))
        
    def test_add_filter_2(self):      
        fact_data = {"q": "question",
                     "a": "answer"}
        card_type_1 = self.card_type_by_id("1")
        card = self.controller().create_new_cards(fact_data, card_type_1,
            grade=-1, tag_names=["default"])[0]

        class MyFilter(Filter):
            def run(self, text):
                return "666"

        self.render_chain().register_filter(MyFilter, in_front=True)
        assert "666" in card.question()
        
        assert type(self.render_chain()._filters[0]) \
               == type(MyFilter(self.mnemosyne.component_manager))

    def test_add_card_type_renderer(self):
        fact_data = {"q": "question",
                     "a": "answer"}
        card_type_1 = self.card_type_by_id("1")
        card = self.controller().create_new_cards(fact_data, card_type_1,
            grade=-1, tag_names=["default"])[0]

        class MyRenderer(Renderer):
            used_for = card_type_1
            def render_fields(self, data, fields, card_type, **render_args):
                return "666"        

        self.render_chain().register_renderer(MyRenderer)
        assert "666" in card.question()
        
        card_type_2 = self.card_type_by_id("2")
        card = self.controller().create_new_cards(fact_data, card_type_2,
            grade=-1, tag_names=["default"])[0]
        assert "666" not in card.question()
