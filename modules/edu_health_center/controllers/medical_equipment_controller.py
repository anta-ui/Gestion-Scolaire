def _api_dict(self):
    return {
        'id': self.id,
        'name': self.name,
        'equipment_type': self.equipment_type,
        'model': self.model,
        'serial_number': self.serial_number,
        'manufacturer': self.manufacturer,
        'purchase_date': str(self.purchase_date) if self.purchase_date else None,
        'warranty_expiry': str(self.warranty_expiry) if self.warranty_expiry else None,
        'state': self.state,
        'location': self.location,
        'responsible_user': self.responsible_user.name if self.responsible_user else None,
        'last_used_date': str(self.last_used_date) if self.last_used_date else None,
        'total_usage_hours': self.total_usage_hours,
        'description': self.description,
    }
