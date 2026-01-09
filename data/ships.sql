select base_id, name, case when uc.category is null then 'Any' else uc.category end, image
from unit u
left join (
	select * from unit_category 
	where category in ('Galactic Republic', 'Sith', 'Rebel', 'Empire', 'First Order', 'Separatist', 'Bounty Hunter', 'Resistance')
) uc on uc.unit_base_id=u.base_id
where combat_type = 2;
