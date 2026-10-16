from asn1crypto import cms, core, x509

# 1. Define CAdES SignerAttribute wrapper structures
class ClaimedAttributes(core.SequenceOf):
    _child_spec = cms.CMSAttribute

class SignerAttributeChoice(core.Choice):
    _alternatives = [
        ('claimed_attributes', ClaimedAttributes, {'implicit': 0}),
    ]

class SignerAttribute(core.SequenceOf):
    _child_spec = SignerAttributeChoice

# 2. Register CAdES SignerAttribute OID
cms.CMSAttributeType._map['1.2.840.113549.1.9.16.2.12'] = 'signer_attributes'
cms.CMSAttribute._oid_specs['signer_attributes'] = SignerAttribute

# OID bindings for name parts inside the attribute (using standard X.509 OIDs)
cms.CMSAttributeType._map['2.5.4.12'] = 'title'
cms.CMSAttributeType._map['2.5.4.4'] = 'surname'
cms.CMSAttributeType._map['2.5.4.42'] = 'given_name'

def create_signer_attr_cms() -> cms.CMSAttribute:
    # Build single DirectoryStrings for individual elements
    val_title = x509.DirectoryString({'utf8_string': 'Генеральный директор'})
    val_surname = x509.DirectoryString({'utf8_string': 'Иванов'})
    val_given_name = x509.DirectoryString({'utf8_string': 'Иван Иванович'})

    # Create inner CMSAttributes
    attr_title = cms.CMSAttribute()
    attr_title['type'] = '2.5.4.12'
    attr_title['values'] = [val_title]

    attr_surname = cms.CMSAttribute()
    attr_surname['type'] = '2.5.4.4'
    attr_surname['values'] = [val_surname]
    
    attr_given_name = cms.CMSAttribute()
    attr_given_name['type'] = '2.5.4.42'
    attr_given_name['values'] = [val_given_name]

    # Combine into SignerAttribute container
    attr_choice = SignerAttributeChoice({
        'claimed_attributes': [attr_surname, attr_given_name, attr_title]
    })
    
    # Outer CMS Attribute
    signer_attr = cms.CMSAttribute()
    signer_attr['type'] = 'signer_attributes'
    signer_attr['values'] = [
        [attr_choice] # core.SequenceOf value is a Python list
    ]
    return signer_attr

if __name__ == "__main__":
    cades_attr = create_signer_attr_cms()
    print("ASN.1 Hex Dump for id-aa-ets-signerAttr:")
    print(cades_attr.dump().hex())

