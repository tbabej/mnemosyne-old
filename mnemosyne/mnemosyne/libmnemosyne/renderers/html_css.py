#
# html_css.py <Peter.Bienstman@UGent.be>
#

from mnemosyne.libmnemosyne.renderer import Renderer

# Css table wizardry based on info from
# http://apptools.com/examples/tableheight.php


class HtmlCss(Renderer):

    """Renders the question or the answer as a full webpage using tables.
    Tested on webkit-based browsers.

    We split out the components of the html page in different functions,
    to allow easier reuse by other renderers.
    
    """

    used_for = None  # All card types.
    table_height = "100%"
    
    def __init__(self, component_manager):
        Renderer.__init__(self, component_manager)
        # We cache the css creation to save some time, especially on mobile
        # devices.
        self._css = {} # {card_type.id: css}

    def body_css(self):
        return "body { margin: 0; padding: 0; border: thin solid #8F8F8F; }\n"

    def card_type_css(self, card_type):
        # Set aligment of the table (but not the contents within the table).
        css = "table { height: " + self.table_height + "; width: 100%; "
        alignment = self.config().card_type_property(\
            "alignment", card_type, default="center")
        if alignment == "left":
            css += "margin-left: 0; margin-right: auto; "
        elif alignment == "right":
            css += "margin-left: auto; margin-right: 0; "
        else:
            css += "margin-left: auto; margin-right: auto; "
        # Background colours.
        colour = self.config().card_type_property(\
            "background_colour", card_type)
        if colour:
            colour_string = ("%X" % colour)[2:] # Strip alpha.
            css += "background-color: #%s; " % colour_string      
        css += "}\n"
        # key tags.
        for true_key, proxy_key in card_type.key_format_proxies().iteritems():
            css += "div#%s { " % true_key
            # Set alignment within table cell.
            alignment = self.config().card_type_property(\
                "alignment", card_type, proxy_key, default="center")            
            css += "text-align: %s; " % alignment  
            # Font colours.
            colour = self.config().card_type_property(\
                "font_colour", card_type, proxy_key)
            if colour:
                colour_string = ("%X" % colour)[2:] # Strip alpha.
                css += "color: #%s; " % colour_string
            # Font.
            font_string = self.config().card_type_property(\
                "font", card_type, proxy_key)
            if font_string:
                family,size,x,x,w,i,u,s,x,x = font_string.split(",")
                css += "font-family: \"%s\"; " % family
                css += "font-size: %spt; " % size
                if w == "25":
                    css += "font-weight: light; "
                if w == "75":
                    css += "font-weight: bold; "
                if i == "1":
                    css += "font-style: italic; "
                if i == "2":
                    css += "font-style: oblique; "
                if u == "1":
                    css += "text-decoration: underline; "
                if s == "1":
                    css += "text-decoration: line-through; "               
            css += "}\n"
        return css

    def update(self, card_type):
        self._css[card_type.id] = \
                self.body_css() + self.card_type_css(card_type)
        
    def css(self, card_type):
        if not card_type.id in self._css:
            self.update(card_type)
        return self._css[card_type.id]

    def body(self, data, keys, **render_args):
        html = ""
        for key in keys:
            if key in data and data[key]:
                html += "<div id=\"%s\">%s</div>" % (key, data[key])
        return html
                
    def render_fields(self, data, keys, card_type, **render_args):
        css = self.css(card_type)
        body = self.body(data, keys, **render_args)
        return """
        <html>
        <head>
        <style type="text/css">
        %s
        </style>
        </head>
        <body>
          <table>
            <tr>
              <td>%s</td>
            </tr>
          </table>
        </body>
        </html>""" % (css, body)
    
