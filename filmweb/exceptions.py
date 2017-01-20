# -*- coding: utf-8 -*-

class RequestFailed(Exception):
	pass

"""Some requests (users related mostly) requires being logged, otherwise they gonna raise this"""
class NotAuthenticated(Exception):
	pass
