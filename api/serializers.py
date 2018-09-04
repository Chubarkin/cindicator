class QuestionJsonSerializer:
    @classmethod
    def serialize(cls, objects):
        return [cls._get_obj_dict(obj) for obj in objects]

    @classmethod
    def _get_obj_dict(cls, obj):
        user_answer = obj.get_user_answer()
        return {
            'id': obj.id,
            'title': obj.title,
            'can_edit': user_answer.can_edit() if user_answer else obj.can_answer(),
            'end_time': obj.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            'user_answer': user_answer.value if user_answer else None,
            'real_answer': obj.real_answer
        }
