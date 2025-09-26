# -*- coding: utf-8 -*-
from pytz import country_names
from odoo import SUPERUSER_ID, api, fields, models, _, exceptions
from odoo.exceptions import ValidationError, UserError,RedirectWarning
import re
import logging
import json
import os
from lxml import etree
import stdnum
from stdnum.co.nit import calc_check_digit, compact, format, is_valid, validate
from odoo import models, fields, api
import requests
from datetime import datetime
import requests
import asyncio
_logger = logging.getLogger(__name__)
from odoo.tools.sql import column_exists, create_column
import re


#---------------------------Modelo RES-PARTNER / TERCEROS-------------------------------#
REGIMEN_TRIBUTATE = [
    ("23", "Persona Natural"),
    ("6", "Persona Natural Regimen Simple"),
    ("45", "Persona Natural Autorretenedor"),
    ("7", "Persona Juridica"),
    ("44", "Persona Juridica Regimen Simple"),
    ("25", "Persona Juridica Autorretenedor"),
    ("46", "Empresas de comercio internacional"),
    ("22", "Tercero del Exterior"),
    ("11", "Grandes contribuyentes autorretenedores"),
    ("24", "Grandes contribuyentes no autorretenedores"),
    ("47", "Sociedad sin animo de lucro"),
]

class_dian = [
    ("1", "Normal"),
    ("2", "Exportador"),
    ("3", "Importador"),
    ("7", "Tercero en Zona Franca"),
    ("8", "Importador en Zona Franca"),
    ("9", "Excluidos"),
]

PERSON_TYPE = [("1", "Persona Natural"), ("2", "Persona Juridica")]

TYPE_COMPANY = [("person", "Persona Natural"), ("company", "Persona Juridica")]
class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    type_account = fields.Selection([('A', 'Ahorros'), ('C', 'Corriente')], 'Tipo de Cuenta', required=True, default='A')
    is_main = fields.Boolean('Es Principal')
    
class ResPartner(models.Model):
    _inherit = 'res.partner'
    _order = 'name'
    _rec_names_search = ['complete_name', 'email', 'ref', 'vat', 'company_registry','business_name']  # TODO vat must be sanitized the same way for storing/searching
    #TRACK VISIBILITY OLD FIELDS
    vat = fields.Char(tracking=True)
    street = fields.Char(tracking=True)
    country_id = fields.Many2one(tracking=True)
    state_id = fields.Many2one(tracking=True)
    zip = fields.Char(tracking=True)
    phone = fields.Char(tracking=True)
    mobile = fields.Char(tracking=True)
    email = fields.Char(tracking=True)
    website = fields.Char(tracking=True)
    lang = fields.Selection(tracking=True)
    category_id = fields.Many2many(tracking=True)
    user_id = fields.Many2one(tracking=True)    
    comment = fields.Text(tracking=True)
    name = fields.Char(tracking=True)
    city = fields.Char(string='Descripción ciudad')
    dv = fields.Char(
        string='DV',
        compute='_compute_dv',
        store=True,
    )
    #INFORMACION BASICA
    x_pn_retri = fields.Selection(REGIMEN_TRIBUTATE, string="Regimen de tributacion", default="23")
    class_dian = fields.Selection(class_dian, string="Clasificacion Dian", default="1")
    personType = fields.Selection(PERSON_TYPE, "Tipo de persona", default="1")
    company_type = fields.Selection(TYPE_COMPANY, string="Company Type")

    formatedNit = fields.Char(
        string="NIT Formatted",store=True
    )
    l10n_latam_identification_type_id = fields.Many2one(default=lambda self: self.env.ref("l10n_co.rut", raise_if_not_found=False))

    # l10n_co_document_code = fields.Char(
    #     related="l10n_latam_identification_type_id.l10n_co_document_code", readonly=True
    # )
    vat_co = fields.Char(
        string="Numero RUT/NIT/CC",
    )
    vat_ref = fields.Char(
        string='NIT Formateado',
        compute='_compute_vat_ref',
        store=True,
    )
    vat_vd = fields.Char(
        string=u"Digito Verificación", size=1, tracking=True
    )
    ciiu_id = fields.Many2one(
        string='Actividad CIIU',
        comodel_name='lavish.ciiu',
        help=u'Código industrial internacional uniforme (CIIU)'
    )

    taxes_ids = fields.Many2many(
        string="Customer taxes",
        comodel_name="account.tax",
        relation="partner_tax_sale_rel",
        column1="partner_id",
        column2="tax_id",
        domain="[('type_tax_use','=','sale')]",
        help="Taxes applied for sale.",
    )
    supplier_taxes_ids =  fields.Many2many(
        string="Supplier taxes",
        comodel_name="account.tax",
        relation="partner_tax_purchase_rel",
        column1="partner_id",
        column2="tax_id",
        domain="[('type_tax_use','=','purchase')]",
        help="Taxes applied for purchase.",
    )
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=lambda self: self.env.company.country_id.id)
    dian_representation_type_id = fields.Many2one(
        'dian.type_code',
        'Tipo de representación',
        domain=[('type', '=', 'representation')]
    )
    dian_establishment_type_id = fields.Many2one(
        'dian.type_code',
        'Tipo de establecimiento',
        domain=[('type', '=', 'establishment')]
    )
    dian_obligation_type_ids = fields.Many2many(
        'dian.type_code',
        'partner_dian_obligation_types',
        'partner_id',
        'type_id',
        'Obligaciones y responsabilidades',
        domain=[('type', '=', 'obligation'),
                ('is_required_dian', '=', True)]
    )
    dian_customs_type_ids = fields.Many2many(
        'dian.type_code',
        'partner_dian_customs_types',
        'partner_id', 'type_id',
        'Usuario de Aduanas',
        domain=[('type', '=', 'customs')]
    )
    dian_fiscal_regimen = fields.Selection(
        [('48', 'Responsable del Impuesto sobre las ventas - IVA'),
         ('49', 'No responsables del IVA'), 
        ('04', 'IC'),
        ('ZA', 'IVA en IC'),
         ('No aplica', 'No aplica')],
        'Régimen fiscal',
        default='No aplica'
    )
    dian_tax_scheme_id = fields.Many2one(
        'dian.tax.type',
        'Responsabilidad fiscal'
    )
    business_name = fields.Char(string='Nombre Comercial', tracking=True)
    firs_name = fields.Char(string='Primer nombre', tracking=True)
    second_name = fields.Char(string='Segundo nombre', tracking=True)
    first_lastname = fields.Char(string='Primer apellido', tracking=True)
    second_lastname = fields.Char(string='Segundo apellido', tracking=True)
    is_ica = fields.Boolean(string='Aplicar ICA', tracking=True)
    #UBICACIÓN PRINCIPAL
    work_groups = fields.Many2many('lavish.work_groups', string='Grupos de trabajo', tracking=True, ondelete='restrict')
    sector_id = fields.Many2one('lavish.sectors', string='Sector', tracking=True, ondelete='restrict')
    ciiu_activity = fields.Many2one('lavish.ciiu', string='Códigos CIIU', tracking=True, ondelete='restrict')
    #GRUPO EMPRESARIAL
    is_business_group = fields.Boolean(string='¿Es un Grupo Empresarial?', tracking=True)
    name_business_group = fields.Char(string='Nombre Grupo Empresarial', tracking=True)

    acceptance_data_policy = fields.Boolean(string='Acepta política de tratamiento de datos', tracking=True)
    acceptance_date = fields.Date(string='Fecha de aceptación', tracking=True)
    not_contacted_again = fields.Boolean(string='No volver a ser contactado', tracking=True)
    date_decoupling = fields.Date(string="Fecha de desvinculación", tracking=True)
    reason_desvinculation_text = fields.Text(string='Motivo desvinculación') 
    
    #INFORMACION FINANCIERA
    company_size = fields.Selection([   ('1', 'Mipyme'),
                                        ('2', 'Pyme'),
                                        ('3', 'Mediana'),
                                        ('4', 'Grande')
                                    ], string='Tamaño empresa', tracking=True)

    #INFORMACIÓN CONTACTO
    contact_type = fields.Many2many('lavish.contact_types', string='Tipo de contacto', tracking=True, ondelete='restrict')
    contact_job_title = fields.Many2one('lavish.job_title', string='Cargo', tracking=True, ondelete='restrict')
    contact_area = fields.Many2one('lavish.areas', string='Área', tracking=True, ondelete='restrict')
    
    #INFORMACION FACTURACION ELECTRÓNICA
    email_invoice_electronic = fields.Char(string='Correo electrónico para recepción electrónica de facturas', tracking=True)

    def _auto_init(self):
        """
        Create compute stored fields dv and vat_ref
        here to avoid MemoryError on large databases.
        """
        if not column_exists(self.env.cr, 'res_partner', 'dv'):
            create_column(self.env.cr, 'res_partner', 'dv', 'varchar')
            _logger.info('Created column dv in res_partner')
        if not column_exists(self.env.cr, 'res_partner', 'vat_ref'):
            create_column(self.env.cr, 'res_partner', 'vat_ref', 'varchar')
            _logger.info('Created column vat_ref in res_partner')
        return super()._auto_init()




    @api.model
    def _names_order_default(self):
        return "first_last"

    @api.model
    def _get_names_order(self):
        """Get names order configuration from system parameters.
        You can override this method to read configuration from language,
        country, company or other"""
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("partner_names_order", self._names_order_default())
        )
    @api.depends('vat')
    def _compute_no_same_vat_partner_id(self):
        for partner in self:
            partner.same_vat_partner_id = ""
    
    def _address_fields(self):
        result = super(ResPartner, self)._address_fields()
        result = result + ['city_id']
        return result


    @api.depends('vat_co','vat', 'dv', 'l10n_latam_identification_type_id')
    def _compute_vat_ref(self):
        for partner in self:
            partner.vat_ref = ''
            if partner.l10n_latam_identification_type_id.l10n_co_document_code not in ('rut','national_citizen_id'):
                continue

            try:
                if partner.vat_co:
                    clean_number = ''.join(filter(str.isdigit, partner.vat))
                    if clean_number:
                        formatted_base = format(clean_number)
                        partner.vat_ref = f"{formatted_base}"
            except Exception as e:
                _logger.error(f"Error formateando NIT para partner {partner.id}: {str(e)}")

    @api.depends('vat', 'vat_co', 'l10n_latam_identification_type_id')
    def _compute_dv(self):
        for partner in self:
            partner._onchange_vat_co()
            partner.dv = ''
            if partner.l10n_latam_identification_type_id.l10n_co_document_code not in ('rut','national_citizen_id'):
                continue
                
            try:
                if partner.vat and "-" in partner.vat:
                    partner.dv = partner.vat.split('-')[1]
                elif partner.vat_co:
                    clean_number = ''.join(filter(str.isdigit, partner.vat_co))
                    if clean_number:
                        partner.dv = calc_check_digit(clean_number)
            except Exception as e:
                _logger.error(f"Error calculando DV para partner {partner.id}: {str(e)}")             

    @api.onchange('vat')
    def _onchange_vat(self):
        for partner in self:
            if partner.l10n_latam_identification_type_id.l10n_co_document_code == 'rut' and partner.vat:
                try:
                    if '-' in partner.vat:
                        base_number, _ = partner.vat.split('-')
                        clean_base = ''.join(filter(str.isdigit, base_number))
                        if clean_base:
                            partner.vat_co = clean_base
                    else:
                        clean_number = ''.join(filter(str.isdigit, partner.vat))
                        if len(clean_number) > 9:
                            partner.vat_co = clean_number[:-1]
                except Exception as e:
                    _logger.error(f"Error procesando vat: {str(e)}")

    @api.onchange('vat_co', 'l10n_latam_identification_type_id')
    def _onchange_vat_co(self):
        for partner in self:
            if partner.l10n_latam_identification_type_id.l10n_co_document_code == 'rut' and partner.vat_co:
                try:
                    if '-' in partner.vat_co:
                        base_number, _ = partner.vat_co.split('-')
                        partner.vat_co = ''.join(filter(str.isdigit, base_number))
                    elif len(''.join(filter(str.isdigit, partner.vat_co))) > 9 and partner.is_company and partner.vat_co[0:1] in ['8','9']:
                        clean_number = ''.join(filter(str.isdigit, partner.vat_co))
                        partner.vat_co = clean_number[:-1]

                    clean_number = ''.join(filter(str.isdigit, partner.vat_co))
                    if clean_number:
                        dv = calc_check_digit(clean_number)
                        partner.vat = f"{clean_number}-{dv}"
                except Exception as e:
                    _logger.error(f"Error procesando vat_co: {str(e)}")





    @api.constrains("vat", "l10n_latam_identification_type_id")
    def check_vat(self):
        # check_vat is implemented by base_vat which this localization
        # doesn't directly depend on. It is however automatically
        # installed for Colombia.
        with_vat = self.filtered(
            lambda x: x.l10n_latam_identification_type_id.is_vat
            and x.country_id.code != "CO"
        )
        return super(ResPartner, with_vat).check_vat()

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if self._context.get('search_by_vat', False):
            if name:
                args = args if args else []
                args.extend(['|', ['name', 'ilike', name], ['vat', 'ilike', name]])
                name = ''
        return super(ResPartner, self).name_search(name=name, args=args, operator=operator, limit=limit)

    @api.depends('complete_name', 'email', 'vat', 'state_id', 'country_id', 
                'commercial_company_name', 'business_name', 'company_type')
    @api.depends_context('show_address', 'partner_show_db_id', 'address_inline', 
                        'show_email', 'show_vat', 'lang')
    def _compute_display_name(self):
        for partner in self:
            name = partner.with_context(lang=self.env.lang)._get_complete_name()
            if partner.business_name:
                if partner.company_type == 'person':
                    name = f"{name} ({partner.business_name})"
                elif partner.company_type == 'company':
                    if name != partner.business_name:
                        name = f"{partner.business_name} [{name}]"
            if partner._context.get('show_address'):
                address = partner._display_address(without_company=True)
                if address:
                    name = f"{name}\n{address}"
            name = re.sub(r'\s+\n', '\n', name)
            if partner._context.get('partner_show_db_id'):
                name = f"{name} ({partner.id})"
            if partner._context.get('address_inline'):
                splitted_names = name.split("\n")
                name = ", ".join([n for n in splitted_names if n.strip()])
            if partner._context.get('show_email') and partner.email:
                name = f"{name} <{partner.email}>"
            if partner._context.get('show_vat') and partner.vat:
                name = f"{name} ‒ {partner.vat}"
            partner.display_name = name.strip()


    def _display_address(self, without_company=False):
        """
        The purpose of this function is to build and return an address formatted accordingly to the
        standards of the country where it belongs.
        :param address: browse record of the res.partner to format
        :returns: the address formatted in a display that fit its country habits (or the default ones
            if not country is specified)
        :rtype: string
        """
        # get the information that will be injected into the display format
        # get the address format
        address_format = self._get_address_format()
        args = {
            "state_code": self.state_id.code or "",
            "state_name": self.state_id.name or "",
            "country_code": self.country_id.code or "",
            "country_name": self._get_country_name(),
            "company_name": self.commercial_company_name or "",
        }
        for field in self._formatting_address_fields():
            args[field] = getattr(self, field) or ""
        if without_company:
            args["company_name"] = ""
        elif self.commercial_company_name:
            address_format = "%(company_name)s\n" + address_format

        args["city"] = args["city"].capitalize() + ","
        return address_format % args


    @api.onchange('type_thirdparty')
    def _onchange_type_thirdparty(self):
        for record in self:
            if record.type_thirdparty:
                for i in record.type_thirdparty:
                    if i.id == 2 and record.company_type == 'company':
                        raise UserError(_('Una compañia no puede estar catalogada como contacto, por favor verificar.')) 


    @api.onchange('firs_name', 'second_name', 'first_lastname', 'second_lastname')
    def _onchange_person_names(self):
        if self.company_type == 'person':
            names = [name for name in [self.firs_name, self.second_name, self.first_lastname, self.second_lastname] if name]
            self.name = u' '.join(names)

    @api.depends('company_type', 'name', 'firs_name', 'second_name', 'first_lastname', 'second_lastname')
    def copy(self, default=None):
        default = default or {}
        if self.company_type == 'person':
            default.update({
                'firs_name': self.firs_name and self.firs_name + _('(copy)') or '',
                'second_name': self.second_name and self.second_name + _('(copy)') or '',
                'first_lastname': self.first_lastname and self.first_lastname + _('(copy)') or '',
                'second_lastname': self.second_lastname and self.second_lastname + _('(copy)') or '',
            })
        return super(ResPartner, self).copy(default=default)


    @api.constrains('bank_ids')
    def _check_bank_ids(self):
        for record in self:
            if len(record.bank_ids) > 0:
                count_main = 0
                for bank in record.bank_ids:
                    count_main += 1 if bank.is_main else 0
                #if count_main > 1:
                #    raise ValidationError(_('No puede tener más de una cuenta principal, por favor verificar.'))

    @api.model
    def ___fields_view_get_address(self, arch):
        arch = super(ResPartner, self)._fields_view_get_address(arch)
        # render the partner address accordingly to address_view_id
        doc = etree.fromstring(arch)
        def _arch_location(node):
            in_subview = False
            view_type = False
            parent = node.getparent()
            while parent is not None and (not view_type or not in_subview):
                if parent.tag == "field":
                    in_subview = True
                elif parent.tag in ["form"]:
                    view_type = parent.tag
                parent = parent.getparent()
            return {
                "view_type": view_type,
                "in_subview": in_subview,
            }

        for city_node in doc.xpath("//field[@name='city']"):
            location = _arch_location(city_node)
            if location["view_type"] == "form" or not location["in_subview"]:
                parent = city_node.getparent()
                parent.remove(city_node)

        arch = etree.tostring(doc, encoding="unicode")
        return arch


class ResCountry(models.Model):
    _inherit = 'res.country'


    name_iso = fields.Char()
    three_iso = fields.Char()
    numeric_code = fields.Char()
    dian_code = fields.Char()
    

class ResCountryState(models.Model):
    _inherit = 'res.country.state'


    def name_get(self):
        rec = []
        for recs in self:
            name = '%s [%s]' % (recs.name or '', recs.code or '')
            rec += [ (recs.id, name) ]
        return rec
    
    @api.depends('name', 'code')
    def _compute_display_name(self):
        for template in self:
            template.display_name = False if not template.name else (
                '{}{}'.format(
                    template.code and '[%s] ' % template.code or '', template.name
                ))
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100,order=None):
        """
        Se hereda metodo name search y se sobreescribe para hacer la busqueda 
        por el codigo del estado/departamento
        """
        if not args:
            args = []
        args = args[:]
        ids = []
        if name:
            ids = self.search([('code', '=like', name + "%")] + args, limit=limit)
            if not ids:
                ids = self.search([('name', operator, name)] + args,limit=limit)
        else:
            ids = self.search(args, limit=100)

        if ids:
            return ids.name_get()
        return self.name_get()

class ResCity(models.Model):
    _inherit = 'res.city'

    name = fields.Char(translate=False)
    code_dian = fields.Char(string="Code")

    def name_get(self):
        rec = []
        for recs in self:
            name = '%s / %s [%s]' % (recs.name or '', recs.state_id.name or '', recs.code or '')
            rec += [ (recs.id, name) ]
        return rec

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for template in self:
            template.display_name = False if not template.name else (
                '{}{}'.format(
                    template.code and '[%s] ' % template.code or '', template.name
                ))
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Se hereda metodo name search y se sobreescribe para hacer la busqueda 
        por el codigo de la ciudad
        """
        if not args:
            args = []
        args = args[:]
        ids = []
        if name:
            ids = self.search([('code', '=like', name + "%")] + args, limit=limit)
            if not ids:
                ids = self.search([('name', operator, name)] + args,limit=limit)
        else:
            ids = self.search(args, limit=100)

        if ids:
            return ids.name_get()
        return self.name_get()

class ResBank(models.Model):
    _inherit = 'res.bank'

    city_id = fields.Many2one('res.city', string="City of Address")
    bank_code = fields.Char(string='Bank Code')            

class ResCompany(models.Model):
    _inherit = 'res.company'

    def _get_default_partner(self):
        res_partner = self.env['res.partner'].sudo()
        partner_id = res_partner.browse(1)
        return partner_id.id

    city_id = fields.Many2one('res.city', string="City of Address")
    vat_vd = fields.Integer(string="Verification digit")
    default_partner_id = fields.Many2one('res.partner', string="Default partner", required=True, default=_get_default_partner)

    default_taxes_ids = fields.Many2many(
        string="Customer taxes",
        comodel_name="account.tax",
        relation="company_default_taxes_rel",
        column1="product_id",
        column2="tax_id",
        domain="[('type_tax_use','=','sale')]",
        help="Taxes applied for sale.",
    )
    default_supplier_taxes_ids = fields.Many2many(
        string="Supplier taxes",
        comodel_name="account.tax",
        relation="company_default_supplier_taxes_rel",
        column1="product_id",
        column2="tax_id",
        domain="[('type_tax_use','=','purchase')]",
        help="Taxes applied for purchase.",
    )

    def _get_company_address_fields(self, partner):
        result = super(ResCompany, self)._get_company_address_fields(partner)
        result['city_id'] = partner.city_id.id
        result['vat_vd'] = partner.vat_vd
        return result

    def _inverse_vat_vd(self):
        for company in self:
            company.partner_id.vat_vd = company.vat_vd
            company.default_partner_id.vat_vd = company.vat_vd


    def _inverse_city_id(self):
        for company in self:
            company.partner_id.city_id = company.city_id
            company.default_partner_id.city_id = company.city_id

    def _inverse_street(self):
        result = super(ResCompany, self)._inverse_street()
        for company in self:
            company.default_partner_id.street = company.street

    def _inverse_country(self):
        result = super(ResCompany, self)._inverse_country()
        for company in self:
            company.default_partner_id.country_id = company.country_id    