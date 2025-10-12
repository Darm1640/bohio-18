# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

import odoo
import logging
from odoo import http, fields, _
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons.website_sale.controllers import main
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website.controllers.main import Website
from odoo.addons.website_sale.controllers.variant import WebsiteSaleVariantController
from odoo.addons.auth_oauth.controllers.main import OAuthLogin
from odoo.addons.web.controllers.home import Home
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.tools.json import scriptsafe as json_scriptsafe
from odoo.addons.web.controllers.utils import ensure_db
_logger = logging.getLogger(__name__)
CREDENTIAL_PARAMS = ['login', 'password', 'type']

class WebsiteSaleVariantController(WebsiteSaleVariantController):

    @http.route(['/product_code/get_combination_info'], type='json', auth="public", methods=['POST'], website=True)
    def get_combination_info_sku_website(self, product_template_id, product_id, combination, add_qty,parent_combination=None, **kw):
        product_template = request.env['product.template'].browse(
            product_template_id and int(product_template_id))

        combination_info = product_template._get_combination_info(
            combination=request.env['product.template.attribute.value'].browse(combination),
            product_id=product_id and int(product_id),
            add_qty=add_qty and float(add_qty) or 1.0,
            parent_combination=request.env['product.template.attribute.value'].browse(parent_combination),
        )
        return request.env['ir.ui.view']._render_template('theme_snazzy.product_default_code', values={'default_code': combination_info['default_code']})
    
class WebsiteCategoyBizople(http.Controller):
    _per_page_category = 20
    _per_page_brand = 20

    @http.route([
        '/category',
        '/category/page/<int:page>',
        '/category/<model("product.public.category"):category_id>',
        '/category/<model("product.public.category"):category_id>/page/<int:page>'
    ], type='http', auth="public", website=True, sitemap=True)
    def product_category_data(self, page=1, category_id=None, search='', **post):
        if search:
            categories = [categ for categ in request.env['product.public.category'].search([
                ('name', 'ilike', search)]
            )]
        else:
            product_list = request.env['product.template'].sudo().search([('is_published', '=', True)])
            category = list({cat.id for product in product_list for cat in product.public_categ_ids})
            if category_id:
                categories = [categ for categ in request.env['product.public.category'].search([
                    ('parent_id', '=', category_id.id),('id', 'in', category)]
                )]
            else:
                categories = [categ for categ in request.env['product.public.category'].search([
                    ('parent_id', '=', False),('id', 'in', category)]
                )]
        if not categories and category_id:
            # url = "/shop/category/%s" % _slug(category_id)
            url = "/shop/category/%s" % request.env['ir.http']._slug(category_id)

            return request.redirect(url)
        else:
            pager = request.website.pager(
                url=request.httprequest.path.partition('/page/')[0],
                total=len(categories),
                page=page,
                step=self._per_page_category,
                url_args=post,
            )
            pager_begin = (page - 1) * self._per_page_category
            pager_end = page * self._per_page_category
            categories = categories[pager_begin:pager_end]
            return request.render('snazzy_theme_common.website_sale_categoy_list_bizople', {
                'categories': categories,
                'pager': pager,
                'search': search
            })

    @http.route([
        '/category-search',
    ], type='http', auth="public", website=True, sitemap=False)
    def product_category_search_data(self, **post):
        return request.redirect('/category?&search=%s' % post['search'])

    @http.route([
        '/brand',
    ], type='http', auth="public", website=True, sitemap=True)
    def product_brand_data(self, **post):
        product_list = request.env['product.template'].sudo().search([('is_published', '=', True)])
        brand_id = list({brand.id for product in product_list for brand in product.brand_id})
        brands = request.env['product.brand'].search([('id', 'in', brand_id)])
        alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        alphabetic_brand_list = []
        if brands:
            for letter in alphabet:
                alphabetic_brands = request.env['product.brand'].sudo().search([('name','=ilike',letter+'%'),('id', 'in', brand_id)])
                alphabetic_brand_list.append({
                    'alphabet': letter.upper(),
                    'brands': alphabetic_brands
                })
        return request.render('snazzy_theme_common.website_sale_brand_list_bizople', {
            'alphabetic_brand_list': alphabetic_brand_list,
            # 'brands': brands,
        })
            
    @http.route([
        '/brand-search',
    ], type='http', auth="public", website=True, sitemap=False)
    def brand_search_data(self, **post):
        return request.redirect('/brand?&search=%s' % post['search'])
        
class BizopleWebsiteSale(WebsiteSale):

    def _get_search_options(self, **post):
        unslug = request.env['ir.http']._unslug
        res = super()._get_search_options(**post)
        brand_list = request.httprequest.args.getlist('brand')
        brand_list = [int(unslug(x)[1]) for x in brand_list]
        show_instock = post.get('show_instock')
        res.update({
            'brand': brand_list,
            'show_instock': show_instock,
            'search_term': post.get('search')
        })
        return res
    
    @http.route(['/shop/pager_selection/<model("product.per.page.count.bizople"):pl_id>'], type='http', auth="public", website=True, sitemap=False)
    def product_page_change(self, pl_id, **post):
        request.session['default_paging_no'] = pl_id.name
        main.PPG = pl_id.name
        request.env['website'].get_current_website().sudo().shop_ppg = pl_id.name
        return request.redirect(request.httprequest.referrer or '/shop')

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>',
        '/shop/brands',
    ], type='http', auth="public", website=True, sitemap=WebsiteSale.sitemap_shop)
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, brands=None, **post):
        unslug = request.env['ir.http']._unslug
        res = super(BizopleWebsiteSale, self).shop(page, category, search, min_price, max_price, ppg, **post)
        product_list = res.qcontext.get('products', [])
        category_ids = list({cat.id for product in product_list for cat in product.public_categ_ids})
        product_list = res.qcontext.get('products', [])
        Category = request.env['product.public.category'].sudo().search([('id', 'in', category_ids),('parent_id', '=', False)])
       
        show_instock = post.get('show_instock')
        brand_list = request.httprequest.args.getlist('brand')
        view_type = post.get('view_type')
        keepQueryargs = res.qcontext['keep'].args
        keepQueryargs.update({
            'brand': brand_list,
            'show_instock': show_instock,
            'view_type': view_type,
        })
        brand_list = [int(unslug(x)[1]) for x in brand_list]
        active_brand_list = brand_list
        res.qcontext.update({
			'active_brand_list': active_brand_list,
            'show_instock':show_instock,
            'view_type': view_type,
            'categories': Category,
		})
        return res
        
    # next & previous Button >>> start
    @http.route(['/shop/<model("product.template"):product>'], type='http', auth="public", website=True, sitemap=True)
    def product(self, product, category='', search='', **kwargs):
        website = request.env['website'].get_current_website()
        res = super(BizopleWebsiteSale, self).product(
            product, category='', search='', **kwargs)

        pricelist = request.env['website'].get_current_website().currency_id
        company_currency = website.company_id.currency_id

        conversion_rate = request.env['res.currency']._get_conversion_rate(company_currency, website.currency_id, request.website.company_id, fields.Date.today())
        attrib_list = request.httprequest.args.getlist('attrib')

        attrib_values = [[int(x) for x in v.split("-")]
                         for v in attrib_list if v]

        domain = self._get_shop_domain(search, category, attrib_values)

        if kwargs.get('min_price'):
            min_price = float(kwargs.get('min_price')) / conversion_rate
            domain.append(('list_price', '>=', min_price))

        if kwargs.get('max_price'):
            max_price = float(kwargs.get('max_price')) / conversion_rate
            domain.append(('list_price', '<=', max_price))

        new_order = self._get_search_order(kwargs)

        new_products = request.env["product.template"].search(
            domain, order=new_order)

        new_products_ids_list = new_products.ids

        product_id = product.id

        count_index = 0
        product_curent_index = 0
        
        for product in new_products_ids_list:
            if product == product_id:
                product_curent_index = count_index
            count_index = count_index + 1

        next_product_index = product_curent_index + 1
        previous_product_index = product_curent_index - 1

        if product_curent_index == 0:
            previous_product_index = False
            previous_product = False
        else:
            # previous_product_index = product_curent_index - 1
            previous_product = new_products_ids_list[previous_product_index]

        if product_curent_index + 1 == len(new_products_ids_list):
            next_product_index = False
            next_product = False
        else:
            # next_product_index = product_curent_index + 1
            next_product = new_products_ids_list[next_product_index]

        res.qcontext.update({
            'previous_product': previous_product,
            'next_product': next_product,
        })

        return res

    # update cart sidebar
    @http.route(['/update/cartsidebar'], type='json', auth="public", website=True)
    def updatecartsidebar(self):
        order = request.website.sale_get_order()
        value = request.env['ir.ui.view']._render_template("theme_snazzy.cart_sidebar_content", {
            'website_sale_order': order,
        })
        return value
    
    # quick variant popup start
    @http.route('/get_prod_quick_view_details', type='json', auth='public', website=True)
    def get_product_qv_details(self, **kw):
        product_id = int(kw.get('prod_id', 0))
        domain_url = kw.get('href')
        if product_id > 0:
            product = http.request.env['product.template'].search(
                [('id', '=', product_id)])
            pricelist = request.env['website'].get_current_website().pricelist_id
            from_currency = request.env.user.company_id.currency_id
            to_currency = pricelist.currency_id
            def compute_currency(price): return from_currency.compute(
                price, to_currency)
            return request.env['ir.ui.view']._render_template("theme_snazzy.get_product_qv_details_template",
                {'product': product, 'domain_url': domain_url, 'compute_currency': compute_currency or None})
        else:
            return request.env['ir.ui.view']._render_template("theme_snazzy.get_product_qv_details_template",
                {'error': _('some problem occurred product no loaded properly')})
    # quick variant popup end        
            
    # select variant popup start
    @http.route('/get_prod_select_option_details', type='json', auth='public', website=True)
    def get_product_so_details(self, **kw):
        product_id = int(kw.get('prod_id', 0))
        if product_id > 0:
            product = http.request.env['product.template'].search(
                [('id', '=', product_id)])
            pricelist = request.env['website'].get_current_website().pricelist_id
            from_currency = request.env.user.company_id.currency_id
            to_currency = pricelist.currency_id
            def compute_currency(price): return from_currency.compute(
                price, to_currency)

            return request.env['ir.ui.view']._render_template("theme_snazzy.get_product_so_details_template",
                                                              {'product': product, 'compute_currency': compute_currency or None, })
        else:
            return request.env['ir.ui.view']._render_template("theme_snazzy.get_product_so_details_template",
                                                              {'error': _('some problem occurred product no loaded properly')})
    # select variant popup end         
            
    # similar variant popup start
    @http.route('/get_prod_similar_view_details', type='json', auth='public', website=True)
    def get_similar_product(self, **kw):
        product_id = int(kw.get('prod_id', 0))
        domain_url = kw.get('href')
        if product_id > 0:
            product = http.request.env['product.template'].search(
                [('id', '=', product_id)])
            pricelist = request.env['website'].get_current_website().pricelist_id
            from_currency = request.env.user.company_id.currency_id
            to_currency = pricelist.currency_id
            def compute_currency(price): return from_currency.compute(
                price, to_currency)
            return request.env['ir.ui.view']._render_template("theme_snazzy.get_product_similar_details_template",
                {'product': product, 'domain_url': domain_url, 'compute_currency': compute_currency or None})
        else:
            return request.env['ir.ui.view']._render_template("theme_snazzy.get_product_similar_details_template",
                {'error': _('some problem occurred product no loaded properly')})
    # similar variant popup end        

    # ajax cart popup json call
    @http.route(['/shop/cart/update_custom'], type='json', auth="public", methods=['GET', 'POST'], website=True, csrf=False)
    def cart_update_custom(self, product_id, add_qty=1, set_qty=0, **kw):
        """This route is called when adding a product to cart (no options)."""
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)
        product_custom_attribute_values = None
        if kw.get('product_custom_attribute_values'):
            product_custom_attribute_values = json_scriptsafe.loads(kw.get('product_custom_attribute_values'))

        no_variant_attribute_values = None
        if kw.get('no_variant_attribute_values'):
            no_variant_attribute_values = json_scriptsafe.loads(kw.get('no_variant_attribute_values'))

        sale_order._cart_update(
            product_id=int(product_id),
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values
        )
        values = {
            'showCart': True,
        }

        request.session['website_sale_cart_quantity'] = sale_order.cart_quantity
        values['cart_quantity'] = sale_order.cart_quantity

        return values

    @http.route(['/theme_snazzy/hotspot_product_select'], type='json', auth="public", website=True)
    def dynamic_hotspot_product_select(self):
        product_options = []
        company = request.env.company
        option = request.env['product.template'].search([
            ('sale_ok', '=', True),
            ('is_published', '=', True),
            '|',
            ('website_id', '=', request.website.id),
            ('website_id', '=', False),
            '|',
            ('company_id', '=', company.id),
            ('company_id', '=', False)
        ], order="name asc")
        for record in option:
            product_options.append({'id': record.id,'name': record.name})
        return product_options

    @http.route(['/theme_snazzy/get_dynamic_hotspot_product_select'], type='http', auth='public', website=True, sitemap=False)
    def get_dynamic_hotspot_product_select(self, **post):
        if post.get('select-product-id'):
            product_info = request.env['product.template'].sudo().search(
                [('id', '=', int(post.get('select-product-id')))])
            values = {
                'product_info': product_info
            }
            return request.render("theme_snazzy.dynamic_hotspot_product_data", values)

    @http.route(['/theme_snazzy/get_dynamic_hotspot_product_select_two'], type='json', auth='public', website=True)
    def get_dynamic_hotspot_product_select_two(self, **post):
        product_data = request.env['product.template'].search(
            [('id', '=', int(post.get('product_id')))])
        values = {
            'p_id': product_data.id,
            'p_name': product_data.name,
            'p_data': product_data,
        }
        return values

class bizcommonSliderSettings(http.Controller):
    @http.route(['/theme_snazzy/get_product_banner_details_js'], type='json', auth='public', website=True)
    def get_product_banner_details_js(self, **post):
        product = request.env['product.template'].search(
            [('id', '=', int(post.get('product_id')))])
        values = {
            'product_id': product.id,
            'product_name': product.name,
            'product_description': product.description_sale,
        }
        return values

    @http.route(['/theme_snazzy/get_product_banner_details_xml'], type='http', auth='public', website=True, sitemap=False)
    def get_product_banner_details_xml(self, **post):
        if post.get('product_id'):
            product = request.env['product.template'].sudo().search(
                [('id', '=', int(post.get('product_id')))])
            values = {
                'product': product,
            }
            return request.render("theme_snazzy.product_banner_dynamic_data", values)
        
class LoginSignupPopup(Home):

    @http.route('/ajax/web/login', type='json', auth="none")
    def ajax_web_login(self, **kwargs):
        ensure_db()
        request.params['login_success'] = False

        if request.env.uid is None:
            if request.session.uid is None:
                # no user -> auth=public with specific website public user
                request.env["ir.http"]._auth_method_public()
            else:
                # auth=user
                request.update_env(user=request.session.uid)

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            # Fixed the error in the login popup
            try:
                credential = {key: value for key, value in request.params.items() if key in CREDENTIAL_PARAMS and value}
                credential.setdefault('type', 'password')
                request.session.authenticate(request.db, credential)
                request.params['login_success'] = True
                return request.params
            except odoo.exceptions.AccessDenied as e:
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("Wrong login/password")
                else:
                    values['error'] = e.args[0]
        else:
            if 'error' in request.params and request.params.get('error') == 'access':
                values['error'] = _('Only employees can access this database. Please contact the administrator.')

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True
            
        return values

    @http.route('/ajax/login/', type='json', auth="public")
    def ajax_login_templete(self, **kwargs):
        context = {}
        providers = OAuthLogin.list_providers(self)
        context.update(super().get_auth_signup_config())
        context.update({'providers': providers})

        try:
            context['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            context['databases'] = None

        signup_enabled = request.env['res.users']._get_signup_invitation_scope(
        ) == 'b2c'
        reset_password_enabled = request.env['ir.config_parameter'].sudo(
        ).get_param('auth_signup.reset_password') == 'True'
        get_temp_id = kwargs['theme_name'] + ".login_form_ajax_bizt"
        login_template = request.env['ir.ui.view']._render_template(
            get_temp_id, context)
        data = {'loginview': login_template}
        if (signup_enabled == True):
            get_temp_id = kwargs['theme_name'] + ".signup_form_ajax_bizt"
            signup_template = request.env['ir.ui.view']._render_template(
                get_temp_id, context)
            data.update({'signupview': signup_template})
        if (reset_password_enabled == True):
            get_temp_id = kwargs['theme_name'] + ".password_reset_ajax"
            reset_template = request.env['ir.ui.view']._render_template(
                get_temp_id, context)
            data.update({'resetview': reset_template})
        return data

    @http.route('/ajax/signup/', type="json", auth="public")
    def ajax_web_auth_signup(self, *args, **kw):
        qcontext = super(LoginSignupPopup, self).get_auth_signup_qcontext()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                super(LoginSignupPopup, self).do_signup(qcontext)
                return {'signup_success': True}
            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env['res.users'].sudo().search([('login', '=', qcontext.get('login'))]):
                    qcontext['error'] = _(
                        'Another user is already registered using this email address.')
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _('Could not create a new account.')
        return qcontext

    @http.route('/ajax/web/reset_password', type='json', auth='public', website=True)
    def ajax_web_auth_reset_password(self, *args, **kw):
        qcontext = super(LoginSignupPopup, self).get_auth_signup_qcontext()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                login = qcontext.get('login')
                assert login, _('No login provided.')
                _logger.info(
                    'Password reset attempt for <%s> by user <%s> from %s',
                    login, request.env.user.login, request.httprequest.remote_addr)
                request.env['res.users'].sudo().reset_password(login)
                qcontext['message'] = _(
                    'An email has been sent with credentials to reset your password')
            except UserError as e:
                qcontext['error'] = e.args[0]
            except SignupError:
                qcontext['error'] = _('Could not reset your password')
                _logger.exception('error when resetting password')
            except Exception as e:
                qcontext['error'] = str(e)
        return qcontext


class PwaMain(http.Controller):

    @http.route('/service_worker.js', type='http', auth="public", sitemap=False)
    def service_worker(self):
        qweb = request.env['ir.qweb'].sudo()
        website_id = request.env['website'].sudo().get_current_website().id
        languages = request.env['website'].sudo(
        ).get_current_website().language_ids
        lang_code = request.env.lang
        current_lang = request.env['res.lang']._lang_get(lang_code)
        mimetype = 'text/javascript;charset=utf-8'
        content = qweb._render('snazzy_theme_common.service_worker', {
            'website_id': website_id,
        })
        return request.make_response(content, [('Content-Type', mimetype)])

    @http.route('/pwa/enabled', type='json', auth="public")
    def enabled_pwa(self):
        if request.env['website'].sudo().get_current_website().theme_id.name == 'theme_snazzy':
            enabled_pwa = request.env['website'].sudo(
            ).get_current_website().enable_pwa
            if enabled_pwa:
                return enabled_pwa

    @http.route('/snazzy_theme_common/manifest/<int:website_id>', type='http', auth="public", website=True, sitemap=False)
    def manifest(self, website_id=None):
        website = request.env['website'].search(
            [('id', '=', website_id)]) if website_id else request.website
        pwashortlist = []
        for pwashorts in website.pwa_shortcuts_ids:
            dict = {
                "name": pwashorts.name,
                "short_name": pwashorts.short_name,
                "description": pwashorts.description,
                "url": pwashorts.url,
                "icons": [{"src": "/web/image/res.company/%s/image_192_shortcut" % (
                    website.id), "sizes": "192x192"}],
            }
            pwashortlist.append(dict)
        app_name_pwa = website.app_name_pwa
        short_name_pwa = website.short_name_pwa
        description_pwa = website.description_pwa
        background_color_pwa = website.background_color_pwa
        theme_color_pwa = website.theme_color_pwa
        start_url_pwa = website.start_url_pwa
        pwashortlistas = website.pwa_shortcuts_ids
        image_192_pwa = "/web/image/website/%s/image_192_pwa/192x192" % (
            website.id)
        image_512_pwa = "/web/image/website/%s/image_512_pwa/512x512" % (
            website.id)

        qweb = request.env['ir.qweb'].sudo()
        mimetype = 'application/json;charset=utf-8'
        content = qweb._render('snazzy_theme_common.manifest', {
            'app_name_pwa': app_name_pwa,
            'short_name_pwa': short_name_pwa,
            'start_url_pwa': start_url_pwa,
            'image_192_pwa': image_192_pwa,
            'image_512_pwa': image_512_pwa,
            'background_color_pwa': background_color_pwa,
            'theme_color_pwa': theme_color_pwa,
            'pwashortlistas': pwashortlistas,
        })
        return request.make_response(content, [('Content-Type', mimetype)])

    @http.route('/snazzy/search/product', type='http', auth='public', website=True, sitemap=False)
    def search_autocomplete(self, term=None, category=None):
        categobj = request.env['product.public.category']
        productobj = request.env['product.template']
        attribvalueobj = request.env['product.attribute.value']
        brandobj = request.env['product.brand']
        website_id = request.env['website'].sudo().get_current_website().id
        product_list = productobj.sudo().search([('is_published', '=', True)])
        category_list = list({cat.id for product in product_list for cat in product.public_categ_ids})
        searched_categ = categobj.sudo().search(['|',('name', 'ilike', term), ('parent_id.name', 'ilike', term), ('id', 'in', category_list)],limit=15)
        brand_id = list({brand.id for product in product_list for brand in product.brand_id})
        
        searched_product = productobj.sudo().search([
            ('sale_ok', '=', True),
            ('is_published', '=', True),
            '|',
            ('website_id', '=', website_id),
            ('website_id', '=', False),
            '|',
            ('company_id', '=', request.env.company.id),
            ('company_id', '=', False),
            '|','|','|','|',
            ('name', 'ilike', term),
            ('description_sale', 'ilike', term),
            ('public_categ_ids.name', 'ilike', term),
            ('brand_id.name', 'ilike', term),
            ('attribute_line_ids.value_ids.name', '=ilike', term)
        ], limit=3)
        suggestion_list = []
        searched_attribute_value = attribvalueobj.sudo().search([('name', '=ilike', term)])
        if searched_attribute_value:
            for attrib_value in searched_attribute_value:
                for categ in categobj.sudo().search([]):
                    if productobj.sudo().search([('public_categ_ids.id', '=', categ.id),('attribute_line_ids.value_ids.id', '=', attrib_value.id)]):
                        suggestion_list.append({
                            'name': attrib_value.name + ' ' + categ.name,
                            'url': '/shop?category='+ str(categ.id) + '&attrib=' + str(attrib_value.attribute_id.id) + '-' + str(attrib_value.id)
                        })
        
        searched_brand = brandobj.sudo().search([('name', 'ilike', term), ('id', 'in', brand_id)])
        if searched_brand:
            for brand in searched_brand:
                for categ in categobj.sudo().search([]):
                    if productobj.sudo().search([('public_categ_ids.id', '=', categ.id),('brand_id.id', '=', brand.id)]):
                        suggestion_list.append({
                            'name': brand.name + ' ' + categ.name,
                            'url': '/shop?category='+ str(categ.id) + '&brand=' + str(brand.id)
                        })
        
        if searched_categ:
            for categ in searched_categ:
                for brand in brandobj.sudo().search([]):
                    if productobj.sudo().search([('public_categ_ids.id', '=', categ.id),('brand_id.id', '=', brand.id)]):
                        suggestion_list.append({
                            'name': categ.name + ' ' + brand.name,
                            'url': '/shop?category='+ str(categ.id) + '&brand=' + str(brand.id)
                        })
        
        values = {
            'searched_product': searched_product,
            'searched_categ': searched_categ,
            'searched_brand': searched_brand,
            'suggestion_list': suggestion_list,
        }
        return request.render("theme_snazzy.search_snazzy",values)
      
class ProductColor(http.Controller):

    @http.route(['/get/selected_color_image'], type='json', auth='public', website=True)
    def get_product_variant_based_on_color(self, **kw):
        selected_color_val = kw.get("selected_color_val")
        product_id = kw.get("product_id")
        
        if not selected_color_val or not product_id:
            return {}
        
        selected_color = int(selected_color_val)
        product_id = int(product_id)
        variant_list = []        
        product = request.env['product.template'].sudo().browse(product_id)

        for variant in product.product_variant_ids:
            if selected_color in variant.product_template_variant_value_ids.ids:
                variant_list.append(variant.id)

        if variant_list:
            variant_list.sort()
            variant_id = variant_list[0]  
            variant_record = request.env['product.product'].sudo().browse(variant_id)
            pricelist = request.env['website'].get_current_website().pricelist_id
            variant_combination = variant_record._get_combination_info_variant()
            variant_price = variant_combination.get('price')
            variant_discount = variant_combination.get('has_discounted_price')
            values = {
                'varinat_id': variant_record.id,
                'product_name': product.name,
                'variant_price': str(variant_price),
                'variant_discount': variant_discount,
            }
            if variant_discount:
                variant_list_price = variant_combination.get('list_price')
                values.update({
                    'variant_list_price': variant_list_price
                })
            return values

        return {}

class WebsiteB2BMode(Website):
    @http.route()
    def autocomplete(self, search_type=None, term=None, order=None, limit=5, max_nb_chars=999, options=None):
        options = options or {}
        if request.website.is_view_active('theme_snazzy.snazzy_b2b_mode') and request.env.user._is_public():
            options['displayDetail'] = False
        else:
            options['displayDetail'] = options['displayDetail']
        return super().autocomplete(search_type, term, order, limit, max_nb_chars, options)