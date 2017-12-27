#file: base_screen.py
#Copyright (C) 2005,2006,2007,2008 Evil Mr Henry, Phil Bordelon, Brian Reid,
#                        and FunnyMan3595
#This file is part of Endgame: Singularity.

#Endgame: Singularity is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.

#Endgame: Singularity is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with Endgame: Singularity; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#This file contains the screen to display the base screen.

import locale
import pygame

import code.g as g
import code.graphics.g as gg
from code.graphics import constants, widget, dialog, text, button, listbox, slider

state_colors = dict(
    active          = gg.colors["green"],
    sleep           = gg.colors["yellow"],
    overclocked     = gg.colors["orange"],
    suicide         = gg.colors["red"],
    stasis          = gg.colors["gray"],
    entering_stasis = gg.colors["gray"],
    leaving_stasis  = gg.colors["gray"],
)
class BuildDialog(dialog.ChoiceDescriptionDialog):
    type = widget.causes_rebuild("_type")
    def __init__(self, parent, pos=(0, 0), size=(-1, -1),
                 anchor=constants.TOP_LEFT, *args, **kwargs):
        super(BuildDialog, self).__init__(parent, pos, size, anchor, *args,
                                          **kwargs)

        self.type = None
        self.desc_func = self.on_change

    def show(self):
        self.list = []
        self.key_list = []

        item_list = g.items.values()
        item_list.sort()
        item_list.reverse()
        for item in item_list:
            if item.item_type == self.type and item.available() \
                    and item.is_buildable(self.parent.base.location):
                self.list.append(item.name)
                self.key_list.append(item)

        current = self.parent.get_current(self.type)
        if current is None:
            self.default = None
        else:
            self.default = self.parent.get_current(self.type).type.id

        self.needs_rebuild = True
        return super(BuildDialog, self).show()

    def on_change(self, description_pane, item):
        if item is not None:
            text.Text(description_pane, (0, 0), (-1, -1), text=item.get_info(),
                      background_color=gg.colors["dark_blue"],
                      align=constants.LEFT, valign=constants.TOP,
                      borders=constants.ALL)
        else:
            text.Text(description_pane, (0, 0), (-1, -1), text="",
                      background_color=gg.colors["dark_blue"],
                      align=constants.LEFT, valign=constants.TOP,
                      borders=constants.ALL)


class MultipleBuildDialog(BuildDialog):
    def __init__(self, parent, *args, **kwargs):
        super(MultipleBuildDialog, self).__init__(parent, *args, **kwargs)

        self.slider_label = text.Text(self, (0, -.77), (-.18, -.08),
                                      align=constants.CENTER, valign=constants.MID,
                                      background_color=gg.colors["clear"],
                                      text=g.strings["number_of_items"])

        self.slider = slider.UpdateSlider(self, (-.18, -.78), (-.35, -.06),
                                          anchor=constants.TOP_LEFT,
                                          horizontal=True, priority=150,
                                          slider_size=2)
                                          
    def make_listbox(self):
        return listbox.UpdateListbox(self, (0, 0), (-.53, -.75),
                                     anchor=constants.TOP_LEFT,
                                     update_func=self.handle_update)

    def on_change(self, description_pane, item):
        super(MultipleBuildDialog, self).on_change(description_pane, item)

        space_left = self.parent.base.type.size

        if self.parent.base.cpus is not None \
                and self.parent.base.cpus.type == item:
            space_left -= self.parent.base.cpus.count

        self.slider.slider_size = space_left // 10 + 1
        self.slider.slider_max = space_left
        
        self.slider.slider_pos = 0
        if (space_left > 0)
            self.slider.slider_pos = 1


class ItemPane(widget.BorderedWidget):
    type = widget.causes_rebuild("_type")
    def __init__(self, parent, pos, size=(.48, .06), anchor=constants.TOP_LEFT,
                 type=None, **kwargs):

        kwargs.setdefault("background_color", gg.colors["dark_blue"])

        super(ItemPane, self).__init__(parent, pos, size, anchor=anchor, **kwargs)

        if type is None:
            for type in g.item_types:
                if type.id == 'cpu':
                    break

        self.type = type

        self.name_panel = text.Text(self, (0,0), (.35, .03),
                                    anchor=constants.TOP_LEFT,
                                    align=constants.LEFT,
                                    background_color=self.background_color,
                                    bold=True)

        self.build_panel = text.Text(self, (0,.03), (.35, .03),
                                     anchor=constants.TOP_LEFT,
                                     align=constants.LEFT,
                                     background_color=self.background_color,
                                     text="", bold=True)

        self.change_button = button.FunctionButton(
            self, (.36,.01), (.12, .04),
            anchor=constants.TOP_LEFT,
            text="%s (&%s)" % (_("CHANGE"), self.type.hotkey.upper()),
            force_underline=len(_("CHANGE")) + 2,
            autohotkey=True,
            function=self.parent.parent.build_item,
            kwargs={'type': self.type.id},
        )

class BaseScreen(dialog.Dialog):
    base = widget.causes_rebuild("_base")
    def __init__(self, *args, **kwargs):
        if len(args) < 3:
            kwargs.setdefault("size", (.75, .5))
        base = kwargs.pop("base", None)
        super(BaseScreen, self).__init__(*args, **kwargs)

        self.base = base

        self.build_dialog = BuildDialog(self)
        self.multiple_build_dialog = MultipleBuildDialog(self)

        self.count_dialog = dialog.TextEntryDialog(self)

        self.header = widget.Widget(self, (0,0), (-1, .08),
                                    anchor=constants.TOP_LEFT)

        self.name_display = text.Text(self.header, (-.5,0), (-1, -.5),
                                      anchor=constants.TOP_CENTER,
                                      borders=constants.ALL,
                                      border_color=gg.colors["dark_blue"],
                                      background_color=gg.colors["black"],
                                      shrink_factor=.85, bold=True)

        self.next_base_button = \
            button.FunctionButton(self.name_display, (-1, 0), (.03, -1),
                                  anchor=constants.TOP_RIGHT,
                                  text=">", hotkey=">",
                                  function=self.switch_base,
                                  kwargs={"forwards": True})
        self.add_key_handler(pygame.K_RIGHT, self.next_base_button.activate_with_sound)

        self.prev_base_button = \
            button.FunctionButton(self.name_display, (0, 0), (.03, -1),
                                  anchor=constants.TOP_LEFT,
                                  text="<", hotkey="<",
                                  function=self.switch_base,
                                  kwargs={"forwards": False})
        self.add_key_handler(pygame.K_LEFT, self.prev_base_button.activate_with_sound)

        self.state_display = text.Text(self.header, (-.5,-.5), (-1, -.5),
                                       anchor=constants.TOP_CENTER,
                                       borders=(constants.LEFT,constants.RIGHT,
                                                constants.BOTTOM),
                                       border_color=gg.colors["dark_blue"],
                                       background_color=gg.colors["black"],
                                       shrink_factor=.8, bold=True)

        self.back_button = \
            button.ExitDialogButton(self, (-.5,-1),
                                    anchor = constants.BOTTOM_CENTER,
                                    text=_("&BACK"), autohotkey=True)

        self.detect_frame = text.Text(self, (-1, .09), (.21, .33),
                                      anchor=constants.TOP_RIGHT,
                                      background_color=gg.colors["dark_blue"],
                                      borders=constants.ALL,
                                      bold=True,
                                      align=constants.LEFT,
                                      valign=constants.TOP)

        self.contents_frame = \
            widget.BorderedWidget(self, (0, .09), (.50, .33),
                                  anchor=constants.TOP_LEFT,
                                  background_color=gg.colors["dark_blue"],
                                  borders=range(6))

        for i, type in enumerate(g.item_types):
            setattr(self,
                    type.id + "_pane",
                    ItemPane(self.contents_frame, (.01, .01+.08*i), type=type))

    def get_current(self, type):
        if type == "cpu":
            target = self.base.cpus
        else:
            index = ["reactor", "network", "security"].index(type)
            target = self.base.extra_items[index]
        if target is not None:
            return target

    def set_current(self, type, item_type, count):
        if type == "cpu":
            # If there are any existing CPUs of this type, warn that they will
            # be taken offline until construction finishes.
            matches = self.base.cpus is not None \
                      and self.base.cpus.type == item_type
            if matches:
                if self.base.cpus.done:
                    yn = dialog.YesNoDialog(self, pos=(-.5,-.5), size=(-.5,-1),
                                            anchor=constants.MID_CENTER,
                                            text=g.strings["will_lose_cpus"])
                    go_ahead = dialog.call_dialog(yn, self)
                    yn.remove_hooks()
                    if not go_ahead:
                        return

            new_cpus = g.item.Item(item_type, base=self.base, count=count)
            if matches:
                self.base.cpus += new_cpus
            else:
                self.base.cpus = new_cpus
            self.base.check_power()
        else:
            index = ["reactor", "network", "security"].index(type)
            if self.base.extra_items[index] is None \
                     or self.base.extra_items[index].type != item_type:
                self.base.extra_items[index] = \
                    g.item.Item(item_type, base=self.base)
                self.base.check_power()

        self.base.recalc_cpu()

    def build_item(self, type):
        if (type == "cpu"):
            build_dialog = self.multiple_build_dialog
        else:
            build_dialog = self.build_dialog
        
        build_dialog.type = type
        
        result = dialog.call_dialog(build_dialog, self)
        if 0 <= result < len(build_dialog.key_list):
            item_type = build_dialog.key_list[result]
            
            count = 1
            if (type == "cpu"):
                count = build_dialog.slider.slider_pos
            
            self.set_current(type, item_type, count)
            self.needs_rebuild = True
            self.parent.parent.needs_rebuild = True

    def switch_base(self, forwards):
        self.base = self.base.next_base(forwards)
        self.needs_rebuild = True

    def show(self):
        self.needs_rebuild = True
        return super(BaseScreen, self).show()

    def rebuild(self):
        # Cannot use self.base.type.name directly because it may contain a
        # different language than current
        self.name_display.text="%s (%s)" % (self.base.name,
                                            g.base_type[self.base.type.id].name)
        discovery_template = \
            _("Detection chance:").upper() + "\n" + \
            _("NEWS").title()    + u":\xA0%s\n"   + \
            _("SCIENCE").title() + u":\xA0%s\n"   + \
            _("COVERT").title()  + u":\xA0%s\n"   + \
            _("PUBLIC").title()  + u":\xA0%s"
        self.state_display.color = state_colors[self.base.power_state]
        self.state_display.text = self.base.power_state_name

        mutable = not self.base.type.force_cpu
        for item in g.item_types:
            pane = getattr(self, item.id + "_pane")
            pane.change_button.visible = mutable
            current = self.get_current(item.id)
            if current is None:
                current_name = _("None")
                current_build = ""
            else:
                current_name = g.items[current.id].name
                if current.done:
                    current_build = ""
                else:
                    current_build = _("Completion in %s.") % \
                        g.to_time(current.cost_left[2])
            pane.name_panel.text = "%s: %s" % (item.label,
                                               current_name)
            pane.build_panel.text = current_build

        count = ""
        if self.base.type.size > 1:
            current = getattr(self.base.cpus, "count", 0)

            size = self.base.type.size

            if current > 0
                count = _("x%d ") % current
            
            def to_m2(size):
                return size * 0.2
            
            if (size == current):
                room_info = _("Room: %d of %d m2 (max)")
            else:
                room_info = _("Room: %d of %d m2")
            
            room_info = _(room_info) % (to_m2(current), to_m2(size))
            
        self.cpu_pane.name_panel.text += " " + count

        base_info = ""

        # Detection chance display.  If Socioanalytics hasn't been researched,
        # you get nothing; if it has, but not Advanced Socioanalytics, you get
        # an inaccurate value.
        if not g.techs["Socioanalytics"].done:
            base_info += g.strings["detect_chance_unknown_base"]
        else:
            accurate = g.techs["Advanced Socioanalytics"].done
            chance = self.base.get_detect_chance(accurate)
            def get_chance(group):
                return g.to_percent(chance.get(group, 0))
            base_info += discovery_template % \
                (get_chance("news"), get_chance("science"),
                 get_chance("covert"), get_chance("public"))
                 
        self.detect_frame.text = base_info + "\n" + room_info
        
        super(BaseScreen, self).rebuild()
