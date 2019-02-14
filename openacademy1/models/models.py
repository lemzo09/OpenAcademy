# -*- coding: utf-8 -*-

from datetime import timedelta, date, datetime

from odoo import models, fields, api, exceptions, _, tools



class Course(models.Model):
    _name = 'openacademy1.course'
    _description = "OpenAcademy1 Courses"

    name = fields.Char(string="Title", required=True)
    description = fields.Text()

    responsible_id = fields.Many2one('res.users', ondelete='set null', string="Responsible", index=True)
    session_ids = fields.One2many('openacademy1.session', 'course_id', string="Sessions")

    @api.multi
    def copy(self, default=None):
        default = dict(default or {})

        copied_count = self.search_count(
            [('name', '=like', _(u"Copy of {}%").format(self.name))])
        if not copied_count:
            new_name = _(u"Copy of {}").format(self.name)
        else:
            new_name = _(u"Copy of {} ({})").format(self.name, copied_count)

        default['name'] = new_name
        return super(Course, self).copy(default)

    _sql_constraints = [
        ('name_description_check',
         'CHECK(name != description)',
         "The title of the course should not be the description"),

        ('name_unique',
         'UNIQUE(name)',
         "The course title must be unique"),
    ]


class Session(models.Model):
    _name = 'openacademy1.session'
    _description = "OpenAcademy1 Sessions"

    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True)
    start_date = fields.Date(default=fields.Date.today)
    duration = fields.Float(digits=(6, 2), help="Duration in days")
    seats = fields.Integer(string="Number of seats")
    active = fields.Boolean(default=True)
    color = fields.Integer()
    instructor_id = fields.Many2one('res.partner', domain=['|', ('instructor', '=', True), ('category_id.name', 'ilike', "Teacher")], string="Instructor")

    course_id = fields.Many2one('openacademy1.course', ondelete='cascade', string="Course", required=True)

    attendee_ids = fields.Many2many('res.partner', string="Attendees")

    taken_seats = fields.Float(string="Taken seats", compute='_taken_seats')

    validation_date = fields.Datetime(string="Validation Date")

    # is_show_validation_date = fields.Boolean(string="is show validation date")

    end_date = fields.Datetime(string="End Date", store=True, compute='_get_end_date', inverse='_set_end_date')

    attendees_count = fields.Integer(string="Attendees count", compute='_get_attendees_count', store=True)

    state = fields.Selection([
        ('draft', "Draft"),
        ('confirmed', "Confirmed"),
        ('done', "Done"),
    ], default='draft' , track_visibility='onchange')


    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_confirm(self):
        if self.seats == 0 :
            print("Veuillez remplir le nombre de places")
        else:
            self.state = 'confirmed'

    @api.multi
    def action_done(self):
        self.state = 'done'
        self.validation_date = datetime.now()


    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for r in self:
            if not r.seats:
                r.taken_seats = 0.0
            else:
                r.taken_seats = 100.0 * len(r.attendee_ids) / r.seats

    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': _("Incorrect 'seats' value"),
                    'message': _("The number of available seats may not be negative"),
                },
            }
        if self.seats < len(self.attendee_ids):
            return {
                'warning': {
                    'title': _("Too many attendees"),
                    'message': _("Increase seats or remove excess attendees"),
                },
            }

    # @api.onchange('state')
    # def _is_show_validation_date(self):
    #     if self.state == 'done':
    #         self.is_show_validation_date = True
    #     else:
    #         self.is_show_validation_date = False

    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for r in self:
            if not (r.start_date and r.duration):
                r.end_date = r.start_date
                continue

            # Add duration to start_date, but: Monday + 5 days = Saturday, so
            # subtract one second to get on Friday instead
            start = fields.Datetime.from_string(r.start_date)
            duration = timedelta(days=r.duration, seconds=-1)
            r.end_date = start + duration

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.end_date):
                continue
            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            start_date = fields.Datetime.from_string(r.start_date)
            end_date = fields.Datetime.from_string(r.end_date)
            r.duration = (end_date - start_date).days + 1


    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for r in self:
            r.attendees_count = len(r.attendee_ids)


    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for r in self:
            if r.instructor_id and r.instructor_id in r.attendee_ids:
                raise exceptions.ValidationError(_("A session's instructor can't be an attendee"))


class ReportEventRegistrationQuestions(models.Model):
    _name = "openacademy1.report"
    _auto = False

    session_id = fields.Many2one(comodel_name='openacademy1.session', string='session')
    course_id = fields.Many2one(comodel_name='openacademy1.course', string='course')
    instructor_id = fields.Many2one(comodel_name='openacademy1.session', string='instructor')
    seats = fields.Float("nombre places")

    @api.model_cr
    def init(self):
        """ Event Question main report """
        tools.drop_view_if_exists(self._cr, 'event_question_report')
        self._cr.execute(""" CREATE VIEW event_question_report AS (
            SELECT
                session_t.id as id,
                session_t.id as session_id,
                course_t.id as course_id,
                session_t.instructor_id as instructor_id,
                session_t.seats as seats

            FROM
                openacademy1_session as session_t
            LEFT JOIN
                openacademy1_course as course_t ON course_t.id = session_t.course_id
            LEFT JOIN
                res_partner as instructor_t ON instructor_t.id = session_t.instructor_id

            GROUP BY

            session_t.id,
            course_t.id,
            instructor_id

        )""")