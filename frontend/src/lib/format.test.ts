import { describe, expect, it } from "vitest";
import { CHECK_TYPES, formatDate } from "./format";

describe("format", () => {
  it("contains all MVP check types", () => {
    expect(CHECK_TYPES).toContain("ping");
    expect(CHECK_TYPES).toContain("ssl_expiry");
    expect(CHECK_TYPES).toContain("metric");
    expect(CHECK_TYPES).toContain("snmp");
    expect(CHECK_TYPES).toContain("dns");
    expect(CHECK_TYPES).toContain("ssh");
    expect(CHECK_TYPES).toContain("database");
    expect(CHECK_TYPES).toContain("ssh_command");
    expect(CHECK_TYPES).toContain("imap");
    expect(CHECK_TYPES).toContain("pop3");
    expect(CHECK_TYPES).toContain("ldap");
    expect(CHECK_TYPES).toContain("snmp_traffic");
    expect(CHECK_TYPES).toContain("windows_service");
    expect(CHECK_TYPES.length).toBe(26);
  });

  it("formatDate returns a string", () => {
    expect(typeof formatDate("2026-06-21T10:00:00Z")).toBe("string");
  });
});
