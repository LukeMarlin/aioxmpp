import asyncio
import unittest

import aioxmpp.service as service
import aioxmpp.disco.service as disco_service
import aioxmpp.disco.xso as disco_xso
import aioxmpp.stanza as stanza
import aioxmpp.structs as structs
import aioxmpp.errors as errors

from aioxmpp.utils import namespaces

from ..testutils import (
    make_connected_client,
    run_coroutine,
)


class TestNode(unittest.TestCase):
    def test_init(self):
        n = disco_service.Node()
        self.assertSequenceEqual(
            [],
            list(n.iter_identities())
        )
        self.assertSetEqual(
            {namespaces.xep0030_info},
            set(n.iter_features())
        )
        self.assertSequenceEqual(
            [],
            list(n.iter_items())
        )

    def test_register_feature_adds_the_feature(self):
        n = disco_service.Node()
        n.register_feature("uri:foo")
        self.assertSetEqual(
            {
                "uri:foo",
                namespaces.xep0030_info
            },
            set(n.iter_features())
        )

    def test_register_feature_prohibits_duplicate_registration(self):
        n = disco_service.Node()
        n.register_feature("uri:bar")

        with self.assertRaisesRegexp(ValueError,
                                     "feature already claimed"):
            n.register_feature("uri:bar")

        self.assertSetEqual(
            {
                "uri:bar",
                namespaces.xep0030_info
            },
            set(n.iter_features())
        )

    def test_register_feature_prohibits_registration_of_xep0030_features(self):
        n = disco_service.Node()
        with self.assertRaisesRegexp(ValueError,
                                     "feature already claimed"):
            n.register_feature(namespaces.xep0030_info)

    def test_unregister_feature_removes_the_feature(self):
        n = disco_service.Node()
        n.register_feature("uri:foo")
        n.register_feature("uri:bar")

        self.assertSetEqual(
            {
                "uri:foo",
                "uri:bar",
                namespaces.xep0030_info
            },
            set(n.iter_features())
        )

        n.unregister_feature("uri:foo")

        self.assertSetEqual(
            {
                "uri:bar",
                namespaces.xep0030_info
            },
            set(n.iter_features())
        )

        n.unregister_feature("uri:bar")

        self.assertSetEqual(
            {
                namespaces.xep0030_info
            },
            set(n.iter_features())
        )

    def test_unregister_feature_prohibts_removal_of_nonexistant_feature(self):
        n = disco_service.Node()

        with self.assertRaises(KeyError):
            n.unregister_feature("uri:foo")

    def test_unregister_feature_prohibts_removal_of_xep0030_features(self):
        n = disco_service.Node()

        with self.assertRaises(KeyError):
            n.unregister_feature(namespaces.xep0030_info)

        self.assertSetEqual(
            {
                namespaces.xep0030_info
            },
            set(n.iter_features())
        )

    def test_register_identity_defines_identity(self):
        n = disco_service.Node()

        n.register_identity(
            "client", "pc"
        )

        self.assertSetEqual(
            {
                ("client", "pc", None, None),
            },
            set(n.iter_identities())
        )

    def test_register_identity_prohibits_duplicate_registration(self):
        n = disco_service.Node()

        n.register_identity(
            "client", "pc"
        )

        with self.assertRaisesRegexp(ValueError,
                                     "identity already claimed"):
            n.register_identity("client", "pc")

        self.assertSetEqual(
            {
                ("client", "pc", None, None),
            },
            set(n.iter_identities())
        )

    def test_register_identity_with_names(self):
        n = disco_service.Node()

        n.register_identity(
            "client", "pc",
            names={
                structs.LanguageTag.fromstr("en"): "test identity",
                structs.LanguageTag.fromstr("de"): "Testidentität",
            }
        )

        self.assertSetEqual(
            {
                ("client", "pc",
                 structs.LanguageTag.fromstr("en"), "test identity"),
                ("client", "pc",
                 structs.LanguageTag.fromstr("de"), "Testidentität"),
            },
            set(n.iter_identities())
        )

    def test_unregister_identity_prohibits_removal_of_last_identity(self):
        n = disco_service.Node()

        n.register_identity(
            "client", "pc",
            names={
                structs.LanguageTag.fromstr("en"): "test identity",
                structs.LanguageTag.fromstr("de"): "Testidentität",
            }
        )

        with self.assertRaisesRegexp(ValueError,
                                     "cannot remove last identity"):
            n.unregister_identity(
                "client", "pc",
            )

    def test_unregister_identity_prohibits_removal_of_undeclared_identity(self):
        n = disco_service.Node()

        n.register_identity(
            "client", "pc",
            names={
                structs.LanguageTag.fromstr("en"): "test identity",
                structs.LanguageTag.fromstr("de"): "Testidentität",
            }
        )

        with self.assertRaises(KeyError):
            n.unregister_identity("foo", "bar")

    def test_unregister_identity_removes_identity(self):
        n = disco_service.Node()

        n.register_identity(
            "client", "pc",
            names={
                structs.LanguageTag.fromstr("en"): "test identity",
                structs.LanguageTag.fromstr("de"): "Testidentität",
            }
        )

        n.register_identity(
            "foo", "bar"
        )

        self.assertSetEqual(
            {
                ("client", "pc",
                 structs.LanguageTag.fromstr("en"), "test identity"),
                ("client", "pc",
                 structs.LanguageTag.fromstr("de"), "Testidentität"),
                ("foo", "bar", None, None),
            },
            set(n.iter_identities())
        )

        n.unregister_identity("foo", "bar")

        self.assertSetEqual(
            {
                ("client", "pc",
                 structs.LanguageTag.fromstr("en"), "test identity"),
                ("client", "pc",
                 structs.LanguageTag.fromstr("de"), "Testidentität"),
            },
            set(n.iter_identities())
        )


class TestStaticNode(unittest.TestCase):
    def setUp(self):
        self.n = disco_service.StaticNode()

    def test_is_Node(self):
        self.assertIsInstance(self.n, disco_service.Node)

    def test_add_items(self):
        item1 = disco_xso.Item()
        item2 = disco_xso.Item()
        self.n.items.append(item1)
        self.n.items.append(item2)

        self.assertSequenceEqual(
            [
                item1,
                item2
            ],
            list(self.n.iter_items())
        )


class TestService(unittest.TestCase):
    def setUp(self):
        self.cc = make_connected_client()
        self.s = disco_service.Service(self.cc)
        self.cc.reset_mock()

        self.request_iq = stanza.IQ(
            from_=structs.JID.fromstr("user@foo.example/res1"),
            to=structs.JID.fromstr("user@bar.example/res2"))
        self.request_iq.autoset_id()
        self.request_iq.payload = disco_xso.InfoQuery()

        self.request_items_iq = stanza.IQ(
            from_=structs.JID.fromstr("user@foo.example/res1"),
            to=structs.JID.fromstr("user@bar.example/res2"))
        self.request_items_iq.autoset_id()
        self.request_items_iq.payload = disco_xso.ItemsQuery()

    def test_is_Service_subclass(self):
        self.assertTrue(issubclass(
            disco_service.Service,
            service.Service))

    def test_setup(self):
        cc = make_connected_client()
        s = disco_service.Service(cc)

        self.assertSequenceEqual(
            [
                unittest.mock.call.stream.register_iq_request_coro(
                    "get",
                    disco_xso.InfoQuery,
                    s.handle_info_request
                ),
                unittest.mock.call.stream.register_iq_request_coro(
                    "get",
                    disco_xso.ItemsQuery,
                    s.handle_items_request
                )
            ],
            cc.mock_calls
        )

    def test_shutdown(self):
        run_coroutine(self.s.shutdown())
        self.assertSequenceEqual(
            [
                unittest.mock.call.stream.unregister_iq_request_coro(
                    "get",
                    disco_xso.InfoQuery
                )
            ],
            self.cc.mock_calls
        )

    def test_default_response(self):
        response = run_coroutine(self.s.handle_info_request(self.request_iq))

        self.assertSetEqual(
            {namespaces.xep0030_info},
            set(item.var for item in response.features)
        )

        self.assertSetEqual(
            {
                ("client", "bot",
                 "aioxmpp default identity",
                 structs.LanguageTag.fromstr("en")),
            },
            set((item.category, item.type_,
                 item.name, item.lang) for item in response.identities)
        )

        self.assertFalse(response.node)

    def test_nonexistant_node_response(self):
        self.request_iq.payload.node = "foobar"
        with self.assertRaises(errors.XMPPModifyError) as ctx:
            run_coroutine(self.s.handle_info_request(self.request_iq))

        self.assertEqual(
            (namespaces.stanzas, "item-not-found"),
            ctx.exception.condition
        )

    def test_register_feature_produces_it_in_response(self):
        self.s.register_feature("uri:foo")
        self.s.register_feature("uri:bar")

        response = run_coroutine(self.s.handle_info_request(self.request_iq))

        self.assertSetEqual(
            {"uri:foo", "uri:bar", namespaces.xep0030_info},
            set(item.var for item in response.features)
        )

    def test_unregister_feature_removes_it_from_response(self):
        self.s.register_feature("uri:foo")
        self.s.register_feature("uri:bar")

        self.s.unregister_feature("uri:bar")

        response = run_coroutine(self.s.handle_info_request(self.request_iq))

        self.assertSetEqual(
            {"uri:foo", namespaces.xep0030_info},
            set(item.var for item in response.features)
        )

    def test_unregister_feature_raises_KeyError_if_feature_has_not_been_registered(self):
        with self.assertRaisesRegexp(KeyError, "uri:foo"):
            self.s.unregister_feature("uri:foo")

    def test_unregister_feature_disallows_unregistering_disco_info_feature(self):
        with self.assertRaises(KeyError):
            self.s.unregister_feature(namespaces.xep0030_info)

    def test_register_identity_produces_it_in_response(self):
        self.s.register_identity(
            "client", "pc"
        )
        self.s.register_identity(
            "hierarchy", "branch"
        )

        response = run_coroutine(self.s.handle_info_request(self.request_iq))

        self.assertSetEqual(
            {
                ("client", "pc", None, None),
                ("hierarchy", "branch", None, None),
                ("client", "bot", "aioxmpp default identity",
                 structs.LanguageTag.fromstr("en")),
            },
            set((item.category, item.type_,
                 item.name, item.lang) for item in response.identities)
        )

    def test_unregister_identity_removes_it_from_response(self):
        self.s.register_identity(
            "client", "pc"
        )

        self.s.unregister_identity("client", "bot")

        self.s.register_identity(
            "hierarchy", "branch"
        )

        self.s.unregister_identity("hierarchy", "branch")

        response = run_coroutine(self.s.handle_info_request(self.request_iq))

        self.assertSetEqual(
            {
                ("client", "pc", None, None),
            },
            set((item.category, item.type_,
                 item.name, item.lang) for item in response.identities)
        )

    def test_unregister_identity_raises_KeyError_if_not_registered(self):
        with self.assertRaisesRegexp(KeyError, r"\('client', 'pc'\)"):
            self.s.unregister_identity("client", "pc")

    def test_register_identity_with_names(self):
        self.s.register_identity(
            "client", "pc",
            names={
                structs.LanguageTag.fromstr("en"): "test identity",
                structs.LanguageTag.fromstr("de"): "Testidentität",
            }
        )

        self.s.unregister_identity("client", "bot")

        response = run_coroutine(self.s.handle_info_request(self.request_iq))

        self.assertSetEqual(
            {
                ("client", "pc",
                 "test identity",
                 structs.LanguageTag.fromstr("en")),
                ("client", "pc",
                 "Testidentität",
                 structs.LanguageTag.fromstr("de")),
            },
            set((item.category, item.type_,
                 item.name, item.lang) for item in response.identities)
        )

    def test_register_identity_disallows_duplicates(self):
        self.s.register_identity("client", "pc")
        with self.assertRaisesRegexp(ValueError, "identity already claimed"):
            self.s.register_identity("client", "pc")

    def test_register_feature_disallows_duplicates(self):
        self.s.register_feature("uri:foo")
        with self.assertRaisesRegexp(ValueError, "feature already claimed"):
            self.s.register_feature("uri:foo")
        with self.assertRaisesRegexp(ValueError, "feature already claimed"):
            self.s.register_feature(namespaces.xep0030_info)

    def test_query_info(self):
        to = structs.JID.fromstr("user@foo.example/res1")
        response = disco_xso.InfoQuery()

        self.cc.stream.send_iq_and_wait_for_reply.return_value = response

        result = run_coroutine(
            self.s.query_info(to)
        )

        self.assertIs(result, response)
        self.assertEqual(
            1,
            len(self.cc.stream.send_iq_and_wait_for_reply.mock_calls)
        )

        call, = self.cc.stream.send_iq_and_wait_for_reply.mock_calls
        # call[1] are args
        request_iq, = call[1]

        self.assertEqual(
            to,
            request_iq.to
        )
        self.assertEqual(
            "get",
            request_iq.type_
        )
        self.assertIsInstance(request_iq.payload, disco_xso.InfoQuery)
        self.assertFalse(request_iq.payload.features)
        self.assertFalse(request_iq.payload.identities)
        self.assertIsNone(request_iq.payload.node)

    def test_query_info_with_node(self):
        to = structs.JID.fromstr("user@foo.example/res1")
        response = disco_xso.InfoQuery()

        self.cc.stream.send_iq_and_wait_for_reply.return_value = response

        with self.assertRaises(TypeError):
            self.s.query_info(to, "foobar")

        result = run_coroutine(
            self.s.query_info(to, node="foobar")
        )

        self.assertIs(result, response)
        self.assertEqual(
            1,
            len(self.cc.stream.send_iq_and_wait_for_reply.mock_calls)
        )

        call, = self.cc.stream.send_iq_and_wait_for_reply.mock_calls
        # call[1] are args
        request_iq, = call[1]

        self.assertEqual(
            to,
            request_iq.to
        )
        self.assertEqual(
            "get",
            request_iq.type_
        )
        self.assertIsInstance(request_iq.payload, disco_xso.InfoQuery)
        self.assertFalse(request_iq.payload.features)
        self.assertFalse(request_iq.payload.identities)
        self.assertEqual("foobar", request_iq.payload.node)

    def test_query_info_caches(self):
        to = structs.JID.fromstr("user@foo.example/res1")
        response = disco_xso.InfoQuery()

        self.cc.stream.send_iq_and_wait_for_reply.return_value = response

        with self.assertRaises(TypeError):
            self.s.query_info(to, "foobar")

        result1 = run_coroutine(
            self.s.query_info(to, node="foobar")
        )
        result2 = run_coroutine(
            self.s.query_info(to, node="foobar")
        )

        self.assertIs(result1, response)
        self.assertIs(result2, response)

        self.assertEqual(
            1,
            len(self.cc.stream.send_iq_and_wait_for_reply.mock_calls)
        )

    def test_query_info_cache_override(self):
        to = structs.JID.fromstr("user@foo.example/res1")

        response1 = disco_xso.InfoQuery()
        self.cc.stream.send_iq_and_wait_for_reply.return_value = response1

        with self.assertRaises(TypeError):
            self.s.query_info(to, "foobar")

        result1 = run_coroutine(
            self.s.query_info(to, node="foobar")
        )

        response2 = disco_xso.InfoQuery()
        self.cc.stream.send_iq_and_wait_for_reply.return_value = response2

        result2 = run_coroutine(
            self.s.query_info(to, node="foobar", require_fresh=True)
        )

        self.assertIs(result1, response1)
        self.assertIs(result2, response2)

        self.assertEqual(
            2,
            len(self.cc.stream.send_iq_and_wait_for_reply.mock_calls)
        )

    def test_query_info_cache_clears_on_disconnect(self):
        to = structs.JID.fromstr("user@foo.example/res1")

        response1 = disco_xso.InfoQuery()
        self.cc.stream.send_iq_and_wait_for_reply.return_value = response1

        with self.assertRaises(TypeError):
            self.s.query_info(to, "foobar")

        result1 = run_coroutine(
            self.s.query_info(to, node="foobar")
        )

        self.cc.on_stream_destroyed()

        response2 = disco_xso.InfoQuery()
        self.cc.stream.send_iq_and_wait_for_reply.return_value = response2

        result2 = run_coroutine(
            self.s.query_info(to, node="foobar")
        )

        self.assertIs(result1, response1)
        self.assertIs(result2, response2)

        self.assertEqual(
            2,
            len(self.cc.stream.send_iq_and_wait_for_reply.mock_calls)
        )

    def test_query_info_timeout(self):
        to = structs.JID.fromstr("user@foo.example/res1")
        response = disco_xso.InfoQuery()

        self.cc.stream.send_iq_and_wait_for_reply.delay = 1
        self.cc.stream.send_iq_and_wait_for_reply.return_value = response

        with self.assertRaises(TimeoutError):
            result = run_coroutine(
                self.s.query_info(to, timeout=0.01)
            )

        self.assertSequenceEqual(
            [
                unittest.mock.call(unittest.mock.ANY),
            ],
            self.cc.stream.send_iq_and_wait_for_reply.mock_calls
        )

    def test_query_info_deduplicate_requests(self):
        to = structs.JID.fromstr("user@foo.example/res1")
        response = disco_xso.InfoQuery()

        self.cc.stream.send_iq_and_wait_for_reply.return_value = response

        result = run_coroutine(
            asyncio.gather(
                self.s.query_info(to, timeout=10),
                self.s.query_info(to, timeout=10),
            )
        )

        self.assertIs(result[0], response)
        self.assertIs(result[1], response)

        self.assertSequenceEqual(
            [
                unittest.mock.call(unittest.mock.ANY),
            ],
            self.cc.stream.send_iq_and_wait_for_reply.mock_calls
        )

    def test_query_info_transparent_deduplication_when_cancelled(self):
        to = structs.JID.fromstr("user@foo.example/res1")
        response = disco_xso.InfoQuery()

        self.cc.stream.send_iq_and_wait_for_reply.return_value = response
        self.cc.stream.send_iq_and_wait_for_reply.delay = 0.1

        q1 = asyncio.async(self.s.query_info(to))
        q2 = asyncio.async(self.s.query_info(to))

        run_coroutine(asyncio.sleep(0.05))

        q1.cancel()

        result = run_coroutine(q2)

        self.assertIs(result, response)

        self.assertSequenceEqual(
            [
                unittest.mock.call(unittest.mock.ANY),
                unittest.mock.call(unittest.mock.ANY),
            ],
            self.cc.stream.send_iq_and_wait_for_reply.mock_calls
        )

    def test_mount_node_produces_response(self):
        node = disco_service.StaticNode()
        node.register_identity("hierarchy", "leaf")

        self.s.mount_node("foo", node)

        self.request_iq.payload.node = "foo"
        response = run_coroutine(self.s.handle_info_request(self.request_iq))

        self.assertSetEqual(
            {
                ("hierarchy", "leaf", None, None),
            },
            set((item.category, item.type_,
                 item.name, item.lang) for item in response.identities)
        )

    def test_mount_node_without_identity_produces_item_not_found(self):
        node = disco_service.StaticNode()

        self.s.mount_node("foo", node)

        self.request_iq.payload.node = "foo"
        with self.assertRaises(errors.XMPPModifyError):
            run_coroutine(self.s.handle_info_request(self.request_iq))

    def test_default_items_response(self):
        response = run_coroutine(
            self.s.handle_items_request(self.request_items_iq)
        )
        self.assertIsInstance(response, disco_xso.ItemsQuery)
        self.assertSequenceEqual(
            [],
            response.items
        )

    def test_items_query_returns_item_not_found_for_unknown_node(self):
        self.request_items_iq.payload.node = "foobar"
        with self.assertRaises(errors.XMPPModifyError):
            run_coroutine(
                self.s.handle_items_request(self.request_items_iq)
            )

    def test_items_query_returns_items_of_mounted_node(self):
        item1 = disco_xso.Item()
        item2 = disco_xso.Item()

        node = disco_service.StaticNode()
        node.register_identity("hierarchy", "leaf")
        node.items.append(item1)
        node.items.append(item2)

        self.s.mount_node("foo", node)

        self.request_items_iq.payload.node = "foo"
        response = run_coroutine(
            self.s.handle_items_request(self.request_items_iq)
        )

        self.assertSequenceEqual(
            [item1, item2],
            response.items
        )

    def test_query_items(self):
        to = structs.JID.fromstr("user@foo.example/res1")
        response = disco_xso.ItemsQuery()

        self.cc.stream.send_iq_and_wait_for_reply.return_value = response

        result = run_coroutine(
            self.s.query_items(to)
        )

        self.assertIs(result, response)
        self.assertEqual(
            1,
            len(self.cc.stream.send_iq_and_wait_for_reply.mock_calls)
        )

        call, = self.cc.stream.send_iq_and_wait_for_reply.mock_calls
        # call[1] are args
        request_iq, = call[1]

        self.assertEqual(
            to,
            request_iq.to
        )
        self.assertEqual(
            "get",
            request_iq.type_
        )
        self.assertIsInstance(request_iq.payload, disco_xso.ItemsQuery)
        self.assertFalse(request_iq.payload.items)
        self.assertIsNone(request_iq.payload.node)

    def test_query_items_with_node(self):
        to = structs.JID.fromstr("user@foo.example/res1")
        response = disco_xso.ItemsQuery()

        self.cc.stream.send_iq_and_wait_for_reply.return_value = response

        with self.assertRaises(TypeError):
            self.s.query_items(to, "foobar")

        result = run_coroutine(
            self.s.query_items(to, node="foobar")
        )

        self.assertIs(result, response)
        self.assertEqual(
            1,
            len(self.cc.stream.send_iq_and_wait_for_reply.mock_calls)
        )

        call, = self.cc.stream.send_iq_and_wait_for_reply.mock_calls
        # call[1] are args
        request_iq, = call[1]

        self.assertEqual(
            to,
            request_iq.to
        )
        self.assertEqual(
            "get",
            request_iq.type_
        )
        self.assertIsInstance(request_iq.payload, disco_xso.ItemsQuery)
        self.assertFalse(request_iq.payload.items)
        self.assertEqual("foobar", request_iq.payload.node)

    def test_query_items_caches(self):
        to = structs.JID.fromstr("user@foo.example/res1")
        response = disco_xso.ItemsQuery()

        self.cc.stream.send_iq_and_wait_for_reply.return_value = response

        with self.assertRaises(TypeError):
            self.s.query_items(to, "foobar")

        result1 = run_coroutine(
            self.s.query_items(to, node="foobar")
        )
        result2 = run_coroutine(
            self.s.query_items(to, node="foobar")
        )

        self.assertIs(result1, response)
        self.assertIs(result2, response)

        self.assertEqual(
            1,
            len(self.cc.stream.send_iq_and_wait_for_reply.mock_calls)
        )

    def test_query_items_cache_override(self):
        to = structs.JID.fromstr("user@foo.example/res1")

        response1 = disco_xso.ItemsQuery()
        self.cc.stream.send_iq_and_wait_for_reply.return_value = response1

        with self.assertRaises(TypeError):
            self.s.query_items(to, "foobar")

        result1 = run_coroutine(
            self.s.query_items(to, node="foobar")
        )

        response2 = disco_xso.ItemsQuery()
        self.cc.stream.send_iq_and_wait_for_reply.return_value = response2

        result2 = run_coroutine(
            self.s.query_items(to, node="foobar", require_fresh=True)
        )

        self.assertIs(result1, response1)
        self.assertIs(result2, response2)

        self.assertEqual(
            2,
            len(self.cc.stream.send_iq_and_wait_for_reply.mock_calls)
        )

    def test_query_items_cache_clears_on_disconnect(self):
        to = structs.JID.fromstr("user@foo.example/res1")

        response1 = disco_xso.ItemsQuery()
        self.cc.stream.send_iq_and_wait_for_reply.return_value = response1

        with self.assertRaises(TypeError):
            self.s.query_items(to, "foobar")

        result1 = run_coroutine(
            self.s.query_items(to, node="foobar")
        )

        self.cc.on_stream_destroyed()

        response2 = disco_xso.ItemsQuery()
        self.cc.stream.send_iq_and_wait_for_reply.return_value = response2

        result2 = run_coroutine(
            self.s.query_items(to, node="foobar")
        )

        self.assertIs(result1, response1)
        self.assertIs(result2, response2)

        self.assertEqual(
            2,
            len(self.cc.stream.send_iq_and_wait_for_reply.mock_calls)
        )

    def test_query_items_timeout(self):
        to = structs.JID.fromstr("user@foo.example/res1")
        response = disco_xso.ItemsQuery()

        self.cc.stream.send_iq_and_wait_for_reply.delay = 1
        self.cc.stream.send_iq_and_wait_for_reply.return_value = response

        with self.assertRaises(TimeoutError):
            result = run_coroutine(
                self.s.query_items(to, timeout=0.01)
            )

        self.assertSequenceEqual(
            [
                unittest.mock.call(unittest.mock.ANY),
            ],
            self.cc.stream.send_iq_and_wait_for_reply.mock_calls
        )

    def test_query_items_deduplicate_requests(self):
        to = structs.JID.fromstr("user@foo.example/res1")
        response = disco_xso.ItemsQuery()

        self.cc.stream.send_iq_and_wait_for_reply.return_value = response

        result = run_coroutine(
            asyncio.gather(
                self.s.query_items(to, timeout=10),
                self.s.query_items(to, timeout=10),
            )
        )

        self.assertIs(result[0], response)
        self.assertIs(result[1], response)

        self.assertSequenceEqual(
            [
                unittest.mock.call(unittest.mock.ANY),
            ],
            self.cc.stream.send_iq_and_wait_for_reply.mock_calls
        )

    def test_query_items_transparent_deduplication_when_cancelled(self):
        to = structs.JID.fromstr("user@foo.example/res1")
        response = disco_xso.ItemsQuery()

        self.cc.stream.send_iq_and_wait_for_reply.return_value = response
        self.cc.stream.send_iq_and_wait_for_reply.delay = 0.1

        q1 = asyncio.async(self.s.query_items(to))
        q2 = asyncio.async(self.s.query_items(to))

        run_coroutine(asyncio.sleep(0.05))

        q1.cancel()

        result = run_coroutine(q2)

        self.assertIs(result, response)

        self.assertSequenceEqual(
            [
                unittest.mock.call(unittest.mock.ANY),
                unittest.mock.call(unittest.mock.ANY),
            ],
            self.cc.stream.send_iq_and_wait_for_reply.mock_calls
        )