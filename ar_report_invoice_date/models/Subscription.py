from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import requests
import json

class SaleSubscription(models.Model):
    _inherit = "sale.subscription"


    def _create_pp_fleet_from_subscription(self,record,log):
        if record.x_partner_portal_sync_status == "READY":
            IS_UPDATE_OPERATION = False
            FLEET_ID = None
            if record.x_studio_fleet_id not in (None, '', False):
                FLEET_ID = record.x_studio_fleet_id
                log('Fleet ' + str(record.x_studio_fleet_id) + ' will be updated...', level='info')
                IS_UPDATE_OPERATION = True

              ################ Fleet Feature defaults ################ 
            fleetFeatures = {
                "ManageDrivers": False,
                "InviteSendEmail": True,
                "Reimbursement": False,
                "PrimaryReimbursementSettlement": '',
                "PrimaryReimbursementType": '',
                "PrimaryReimbursementRate": {
                  "currencyCode": "",
                  "amount": 0.0
                },
                "PrimaryReimbursementPartner": '',
                "DisplayCurrency": "GBP",
                "ManageChargePoint": False,
                "ManageSubscriptions": False,
                "PaidCharging": False,
                "ManageBilling": False,
                "AllowSubOrganisations": False,
                "UseLocationServices": False,
                "RequiresUserHomeAddress": False,
                "TemplateName": "Ohme"
            }
          

            payment_term_id = ''
            payment_term_name = ''
          
            if record["payment_term_id"] not in (None, '', False) and record["payment_term_id"]["id"] not in (None, '', False):
                payment_term_id = record["payment_term_id"]["id"]
                payment_term_name = record["payment_term_id"]["name"]
            else:
                raise Warning('Payment Terms not set. Please set and try again!')
            

            # DEFAULTING TO TRUE...  
            # if record.x_invite_send_email not in (None, '', False):
            #   fleetFeatures["InviteSendEmail"] = record.x_invite_send_email
            if record.x_display_currency not in (None, '', False):
                fleetFeatures["DisplayCurrency"] = record.x_display_currency  
            
            if record.x_location_services not in (None, '', False):
                fleetFeatures["UseLocationServices"] = record.x_location_services
            
            if record.x_sub_organisations not in (None, '', False):
                fleetFeatures["AllowSubOrganisations"] = record.x_sub_organisations
              
            if record.x_template_name not in (None, '', False):
                fleetFeatures["TemplateName"] = record.x_template_name
            
            ################ Subscription values ################ 
            subscription = record
          
            #set subscription values
            company_id_ary = subscription['company_id']
            partner_id_arry = subscription['partner_id']
            subscription_currency_id_ary = subscription['currency_id']
            recurring_invoice_line_ids_ary = subscription['recurring_invoice_line_ids']

            fleet_details = {}
            
            subscription_details = {
                "subscription_id": subscription['id'],
                "subscription_code": subscription['code'],
                "subscription_total": subscription['recurring_total'],
                "subscription_recurring_type": subscription['recurring_rule_type'],
                "subscription_currency_id": subscription_currency_id_ary.id,
                "subscription_start_date": subscription['date_start'].strftime('%Y-%m-%d-%H:%M:%S'),
                "subscription_recurring_invoice_line_ids": ','.join([str(x.id) for x in recurring_invoice_line_ids_ary]),
                "payment_terms": {"id": payment_term_id, "name": payment_term_name},
                "partner_id": partner_id_arry.id,
                "partner_name": partner_id_arry.name,
                "company_id": company_id_ary.id
            }
          

            subscription_line_items = []
          
            for invoice_line_id in recurring_invoice_line_ids_ary:

                sli_tmp = self.env['sale.subscription.line'].sudo().search_read(
                    [('id', '=', invoice_line_id.id)],
                    limit=1)    
            
                if len(sli_tmp) > 0:
                    sli = sli_tmp[0]
                    subscription_line_product_id = sli['product_id'][0]
                    subscription_line_product_name = sli['product_id'][1]
          
                if sli['name'].startswith('[OHMEFLEETSUBSTD]'):
                    fleetFeatures["ManageDrivers"] = True
          
                if sli['name'].startswith('[OHMEFLEETREIMBURSE]'):
                    fleetFeatures["Reimbursement"] = True

                    if IS_UPDATE_OPERATION:
                        fleetFeatures["PrimaryReimbursementSettlement"] = record.x_studio_reimbursement_settlement
                        fleetFeatures["PrimaryReimbursementType"] = record.x_studio_reimbursement_type
                        fleetFeatures["PrimaryReimbursementRate"]["currencyCode"] = record.x_studio_reimbursement_currency
                        fleetFeatures["PrimaryReimbursementRate"]["amount"] = record.x_studio_default_reimbursement_rate
                        fleetFeatures["PrimaryReimbursementPartner"] = record.x_studio_reimbursement_partner
                    else:
                        # Insert defaults
                        fleetFeatures["PrimaryReimbursementSettlement"] = ''
                        fleetFeatures["PrimaryReimbursementType"] = ''
                        fleetFeatures["PrimaryReimbursementRate"]["currencyCode"] = ''
                        fleetFeatures["PrimaryReimbursementRate"]["amount"] = 0.0
                        fleetFeatures["PrimaryReimbursementPartner"] = ''

                    if fleetFeatures["PrimaryReimbursementSettlement"] in ('', None, False):
                        fleetFeatures["PrimaryReimbursementSettlement"] = None

                    if fleetFeatures["PrimaryReimbursementType"] in ('', None, False):
                        fleetFeatures["PrimaryReimbursementType"] = None            

                    if fleetFeatures["PrimaryReimbursementRate"]["currencyCode"] in ('', None, False):
                        fleetFeatures["PrimaryReimbursementRate"]["currencyCode"] = ''

                    if fleetFeatures["PrimaryReimbursementRate"]["amount"] in ('', None, False):
                        fleetFeatures["PrimaryReimbursementRate"]["amount"] = 0.0        


                  
                if sli['name'].startswith('[OHMECPOSRV]'):
                    fleetFeatures["ManageChargePoint"] = True
                    fleetFeatures["ManageBilling"] = True
                    fleetFeatures["ManageSubscriptions"] = True
                    fleetFeatures["PaidCharging"] = True   

                subscription_line_items.append({
                    "subscription_line_id": sli['id'],
                    "subscription_line_name": sli['name'],
                    "subscription_line_quantity": sli['quantity'],
                    "subscription_line_price_unit": sli['price_unit'],
                    "subscription_line_price_subtotal": sli['price_subtotal'],
                    "subscription_line_product_id": subscription_line_product_id,
                    "subscription_line_product_name": subscription_line_product_name
                })
          
          
            ################# Main contact for Partner ################ 
            contact_details = {
                "main": None,
                "invoice": None,
                "org": None    
            }
          
            main_contact = self.env['res.partner'].sudo().search_read([('parent_id', '=', subscription_details["partner_id"]),('x_studio_primary_contact', '=', True)],limit=1)
          
            if (len(main_contact) == 0):
                #records.message_post(subject='Error',body='No primary contact found, cannot create Fleet on backend!',partner_ids=[subscription_details["partner_id"]])      
                raise Warning('No primary contact found! (Select the checkbox "Primary Contact" of a contact to make it the Primary Contact!). Fleet NOT created!')
          
            if main_contact[0]['name'] == '' or main_contact[0]['name'] == False:
                raise Warning('No primary contact Name found! Fleet NOT created!')
            
            if main_contact[0]['email'] == '' or main_contact[0]['email'] == False:
                raise Warning('No primary contact Email address found! Fleet NOT created!')    
          
            main_country_code =  ''
            main_country_name =  ''    
            main_country_id =  main_contact[0]['country_id']
          
            # Country code and name
            if main_country_id:
                main_country = self.env['res.country'].sudo().search_read([('id', '=', main_country_id[0])],fields= ["code", "display_name"])        
                main_country_code =  main_country[0]['code']
                main_country_name =  main_country[0]['display_name']
            else:
                main_country_code =  ''
                main_country_name =  ''
          
            # State
            main_state_name = main_contact[0]['state_id']    
          
            if main_contact[0]['state_id']:
                main_state = self.env['res.country.state'].sudo().search_read([('id', '=', main_contact[0]['state_id'])],fields= ['display_name'])
                main_state_name = main_state[0]['display_name']  
          
            contact_details['main'] = {
                'name': main_contact[0]['name'],
                'email': main_contact[0]['email'],
                'full_address': main_contact[0]['contact_address_complete'],
                'street': main_contact[0]['street'],
                'street2': main_contact[0]['street2'],
                'city': main_contact[0]['city'],
                'state': main_state_name,
                'zip': main_contact[0]['zip'],     
                'country':  main_country_name,          
                'country_code':  main_country_code,
                'phone': main_contact[0]['phone']      
            }
          
            ################# Invoice contact for Partner ################ 
            invoice_address = self.env['res.partner'].sudo().search_read([('parent_id', '=', subscription_details["partner_id"]),('type','=','invoice')],)
          
            if (len(invoice_address) > 0):
            
                if invoice_address[0]['name'] == '' or invoice_address[0]['name'] == False:
                    raise Warning('No invoice contact Name found! Fleet NOT created!')
                
                if invoice_address[0]['email'] == '' or invoice_address[0]['email'] == False:
                    raise Warning('No invoice contact Email address found! Fleet NOT created!')      
                
                invoice_country_code =  ''
                invoice_country_name =  ''    
                invoice_country_id =  invoice_address[0]['country_id']
              
                # Country code and name
                if invoice_country_id:
                    invoice_country = self.env['res.country'].sudo().search_read([('id', '=', invoice_country_id[0])],fields= ["code", "display_name"])
                    invoice_country_code =  invoice_country[0]['code']
                    invoice_country_name =  invoice_country[0]['display_name']
                else:
                    invoice_country_code =  ''
                    invoice_country_name =  ''
              
                # State
                invoice_state_name = invoice_address[0]['state_id']    
              
                if invoice_address[0]['state_id']:
                    invoice_state = self.env['res.country.state'].sudo().search_read([('id', '=', invoice_address[0]['state_id'])],fields= ['display_name'])
                    invoice_state_name = invoice_state[0]['display_name']
          
                contact_details["invoice"] = {
                    'name': invoice_address[0]['name'],
                    'email': invoice_address[0]['email'],
                    'full_address': invoice_address[0]['contact_address_complete'],
                    'street': invoice_address[0]['street'],
                    'street2': invoice_address[0]['street2'],
                    'city': invoice_address[0]['city'],
                    'state': invoice_state_name,
                    'zip': invoice_address[0]['zip'],     
                    'country':  invoice_country_name,          
                    'country_code':  invoice_country_code,
                    'phone': invoice_address[0]['phone']       
              }
            else:
                log('Invoice address not found for Partner Id:' + str(subscription_details["partner_id"]), level='info')    
                raise Warning('No invoice contact found! Fleet NOT created!')
              
          
          
            ################# Fleet contact for Partner ################ 
            fleet = self.env['res.partner'].sudo().search_read([('id', '=', subscription_details["partner_id"])])    
          
            if (len(fleet) > 0):
                org_country_code =  ''
                org_country_name =  ''    
                org_country_id =  fleet[0]['country_id']
              
                # Country code and name
                if org_country_id:
                    org_country = self.env['res.country'].sudo().search_read([('id', '=', org_country_id[0])],fields= ["code", "display_name"])
                    org_country_code =  org_country[0]['code']
                    org_country_name =  org_country[0]['display_name']
                else:
                    org_country_code =  ''
                    org_country_name =  ''
              
                # State
                org_state_name = fleet[0]['state_id']    
              
                if fleet[0]['state_id']:
                    org_state = self.env['res.country.state'].sudo().search_read([('id', '=', fleet[0]['state_id'])],fields= ['display_name'])
                    org_state_name = org_state[0]['display_name']    
            
            
                contact_details["org"] = {
                    'name': fleet[0]['name'],
                    'email': fleet[0]['email'],   
                    'full_address': fleet[0]['contact_address_complete'],          
                    'street': fleet[0]['street'],
                    'street2': fleet[0]['street2'],
                    'city': fleet[0]['city'],
                    'state': org_state_name,
                    'zip': fleet[0]['zip'],
                    'country':  org_country_name,              
                    'country_code':  org_country_code,
                    'phone': fleet[0]['phone']
                }
              
                fleet_details['website'] = fleet[0]['website']
                fleet_details['vat'] = fleet[0]['vat']
              
                log('Fleet address :' + json.dumps(contact_details["org"]), level='info')                
            else:
                log('Org address not found!', level='info')     
            
          
          
            ################ Full result ################ 
            result = {
                "odoo": {
                    "db" : record._cr.dbname
                    },
                "fleet": {
                    "details" : fleet_details,
                    "features": fleetFeatures
                },
                "subscription": {
                    "details": subscription_details,
                    "line_items": subscription_line_items
                },
                "contact": contact_details
            }
            log(f'ABOUT TO POST THIS FLEET DATA:\n\n'+json.dumps(result), level='info')          
            
            
            post_endpoint = self.env["ir.config_parameter"].sudo().get_param("ohme.url")
            token = self.env["ir.config_parameter"].sudo().get_param("ohme.token")
            post_headers = {"Authorization": "Basic %s"%(token)}
            if not token or not post_endpoint:
                raise UserError('Please Provide Api Connection Details')
            
            try:
            
                # Use update endpoint ?
                if FLEET_ID is not None:
                    post_endpoint = post_endpoint + FLEET_ID + '/updateFeatures'
                    resp = requests.put(post_endpoint, json = result, headers = post_headers)
                else:
                    resp = requests.post(post_endpoint, json = result, headers = post_headers)

                if resp.status_code == 200 or resp.status_code == 201:
              
                    if FLEET_ID is not None:
                        record.write({'x_partner_portal_sync_status': 'POSTED'})
                        record.message_post(body='Fleet updated on backend')
                        log(f'SUCCESSFULLY UPDATED FLEET:\n\n'+json.dumps(result), level='info')        
                    else:
                        record.write({'x_partner_portal_sync_status': 'POSTED'})
                        record.write({'x_studio_fleet_id': resp.json()['fleetId']})
                        record.message_post(body='Successfully created Fleet on backend!<br/><br/><b>Fleet Id:</b><br/>'+resp.json()['fleetId']+'<br/><br/><b>Invitation Link:</b>\n'+resp.json()['invitationLink'])
                        log(f'SUCCESSFULLY POSTED FLEET:\n\n'+json.dumps(result), level='info')
                else:
                    record.write({'x_partner_portal_sync_status': 'NOT_READY'})
                    log(f'ERROR POSTING FLEET:\n\n'+resp.text, level='error')
                    raise Warning('FLEET CREATION ERROR:\n\n'+resp.text)
                    raise Exception('ERROR posting fleet, see log...')
            except Exception as e:
                log(f'ERROR POSTING FLEET:\n\n'+str(e), level='error')
                record.write({'x_partner_portal_sync_status': 'NOT_READY'})
                raise Warning('FLEET CREATION ERROR:\n\nCODE: '+str(resp.status_code) + '\n\n' + resp.text + '\n\nPAYLOAD WAS:' + str(result))